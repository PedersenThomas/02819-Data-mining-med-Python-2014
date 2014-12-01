import configuration
import json
import time
import Queue

import requests
import matplotlib.pyplot as plt
import networkx as nx

import language2color as ltc

import matplotlib.backends.backend_pdf as pdfs

number_of_repos_to_visit = 10000
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
        print user_repo['full_name']
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
        print len(repo_visited), user['login'], user_queue.qsize()
        try:
            subscriptions_url = user["subscriptions_url"] + "?per_page=100"
            for user_repo in get_content(cfg, subscriptions_url):
                read_repository(user_repo, user_queue, repo_visited)
        except LookupError:
            pass

    non_fork_repos = filter(lambda repo: not repo['fork'], repo_visited)
    draw_languages(non_fork_repos, cfg.graph_save_path)


def draw_languages(dirty_repos, save_path):
    # save_repos_to_file(dirty_repos)
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
                        if pair not in connections:
                            connections[pair] = 0
                        connections[pair] += 1

    # for conn in connections:
    #     G.add_edge(conn[0], conn[1])

    G.add_edges_from(connections)

    node_size = calculate_node_sizes(languages)
    G.add_nodes_from(languages.keys())
    
    labels = {}
    for lang in languages:
        labels[lang] = "(%d) %s" % (len(languages[lang]), lang)

    node_color = [ltc.get_color(lang) for lang in languages]

    edgesize = calculate_edge_sizes(connections)
    
    plt.figure(1,figsize=(20,20))
    nx.draw(G,
            layout=nx.spring_layout(G, iterations=100),
            labels=labels,
            width=edgesize,
            node_size=node_size,
            node_color=node_color,
            linewidths=0.0)

    epoch = time.time()
    save_path += str(epoch) + "_" + str(number_of_repos_to_visit) + ".pdf"


    with pdfs.PdfPages(save_path) as pdf:
        pdf.savefig()

    plt.show()


def calculate_node_sizes(languages, min_size=500, max_size=10000):
    if not languages:
        return []

    highest = max([len(languages[lang]) for lang in languages])
    return [min_size + (max_size - min_size) *
            float(len(languages[lang])) / highest 
            for lang in languages]

def calculate_edge_sizes(connections, max_line_size=10):
    if not connections:
        return []
    
    highest = max([connections[conn] for conn in connections])
    return [max_line_size
            * float(connections[conn])
            / highest for conn in connections]


def save_repos_to_file(repos):
    repo_keys = ["contributors", "language", "fork", "full_name"]
    con_keys = ["login"]

    clean_repos = []
    for repo in repos:
        clean_repo = {}
        for key in repo:
            if key == "contributors":
                clean_contributors = []
                for contributor in repo[key]:
                    clean_contributor = {}
                    for contrib_key in contributor:
                        if contrib_key in con_keys:
                            clean_contributor[contrib_key] = contributor[contrib_key]
                    clean_contributors.append(clean_contributor)
                clean_repo[key] = clean_contributors
            elif key in repo_keys:
                clean_repo[key] = repo[key]
        clean_repos.append(clean_repo)

    text = json.dumps(clean_repos)

    file = open("newfile.txt", "w")

    file.write(text)

    file.close()


if __name__ == '__main__':
    cfg = configuration.Configuration('config.cfg')
    crawl(cfg)

    # file = open("example1.graphdata", "r")
    # repos = json.load(file)
    # draw_languages(repos, cfg.graph_save_path)

    # print cfg.graph_save_path
    # print cfg.graph_start_repos


