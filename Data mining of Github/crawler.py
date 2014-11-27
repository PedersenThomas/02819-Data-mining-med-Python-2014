import configuration
import json
import time
import Queue

import requests
import matplotlib.pyplot as plt
import networkx as nx

import language2color as ltc

import matplotlib.backends.backend_pdf as pdfs

number_of_repos_to_visit = 500
contributer_limit = 3

requests.adapters.DEFAULT_RETRIES = 5


def link_to_dict(link):
    links = link.split(", ")
    dict = {}

    for l in links:
        link_last_idx = l.index(">")
        rel_idx = l.index("rel=") + 5
        dict[l[rel_idx:-1]] = l[1:link_last_idx]

    return dict


def get_content(cfg, url):
    credentials = requests.auth.HTTPBasicAuth(cfg.git_user, cfg.git_password)
    response = requests.get(url,
                            headers={'User-Agent': cfg.user_agent},
                            auth=credentials)
    if response.status_code == 204:
        raise LookupError("page does not contain any content")
    if response.status_code != 200:
        raise LookupError("Page returned an error.")
    if int(response.headers["X-RateLimit-Remaining"]) < 20:
        # Wait
        current_time = time.time()
        reset_time = int(response.headers["X-RateLimit-Reset"])
        time.sleep(reset_time - current_time)

    content = json.loads(response.content)

    if 'link' in response.headers:
        link = link_to_dict(response.headers["link"])
        while "next" in link:
            response = requests.get(link['next'],
                                    headers={'User-Agent': cfg.user_agent},
                                    auth=credentials)
            content = content + json.loads(response.content)
            link = link_to_dict(response.headers['link'])
    return content


def read_repository(user_repo, user_queue, repo_visited):
    # check if repo has already been visited
    if not (user_repo in repo_visited):
        repo_visited.append(user_repo)
        try:
            contributor_url = user_repo["contributors_url"] + "?per_page=100"
            contributors = get_content(cfg, contributor_url)
            user_repo["contributors"] = contributors
            if len(contributors) >= contributer_limit:
                for contributor in contributors:
                    user_queue.put(contributor)
        except LookupError:
            user_repo["contributors"] = []


def is_done(user_queue, repo_visited):
    return user_queue.empty() or len(repo_visited) >= number_of_repos_to_visit


def crawl(cfg):
    user_queue = Queue.Queue()

    repo_visited = [get_content(cfg, start_repo)
                    for start_repo
                    in cfg.graph_start_repos]

    for repo in repo_visited:
        users = get_content(cfg, repo["contributors_url"] + "?per_page=100")
        repo["contributors"] = users

        for user in users:
            user_queue.put(user)

    while not is_done(user_queue, repo_visited):
        user = user_queue.get()
        try:
            subscriptions_url = user["subscriptions_url"] + "?per_page=100"
            for user_repo in get_content(cfg, subscriptions_url):
                read_repository(user_repo, user_queue, repo_visited)
        except LookupError:
            pass

    non_fork_repos = filter(lambda repo: not repo['fork'], repo_visited)
    draw_languages(non_fork_repos, cfg.graph_save_path)


def draw_languages(dirty_repos, save_path):
    G = nx.Graph()
    # Clean out repos without a language.
    repos = filter(lambda repo:
                   'language' in repo and
                   repo['language'] is not None and
                   repo['language'].strip().lower() != 'none', dirty_repos)

    # Divide the repos into Languages.
    languages = {}
    for repo in repos:
        language = repo['language']
        if language not in languages:
            languages[language] = []
        languages[language].append(repo)

    # Find the connections between languages.
    connections = {}
    for a in repos:
        for b in repos:
            if a != b:
                a_users = [user["login"] for user in a["contributors"]]
                b_users = [user["login"] for user in b["contributors"]]
                shared_users = set(a_users).intersection(b_users)
                if len(shared_users) >= contributer_limit:
                    pair = (min(a['language'], b['language']),
                            max(a['language'], b['language']))
                    if pair[0] != pair[1]:
                        print "edge: ", pair
                        if pair not in connections:
                            connections[pair] = 0
                        connections[pair] += 1

    edge_size = []
    for conn in connections:
        G.add_edge(conn[0], conn[1])
        edge_size.append(connections[conn]*5)
        print "connection: ", conn[0], conn[1]

    node_size = []
    labels = {}
    for lang in languages:
        G.add_node(lang)
        labels[lang] = lang
        node_size.append((len(languages[lang])*20)+20)

    node_color = [ltc.get_color(lang) for lang in languages]

    highest_contrib_count = max([connections[conn] for conn in connections])
    max_line_size = 10
    edgesize = [max_line_size
                * float(connections[conn])
                / highest_contrib_count for conn in connections]

    nx.draw(G,
            layout=nx.spring_layout(G, iterations=100),
            labels=labels,
            edge_size=edge_size,
            width=edgesize,
            node_size=node_size,
            node_color=node_color,
            linewidths=0.0)

    epoch = time.time()
    save_path += str(epoch) + "_" + str(number_of_repos_to_visit) + ".pdf"

    with pdfs.PdfPages(save_path) as pdf:
        pdf.savefig()

    plt.show()


if __name__ == '__main__':
    cfg = configuration.Configuration('config.cfg')
    crawl(cfg)

    # print cfg.graph_save_path
    # print cfg.graph_start_repos
