# -*- coding: utf-8 -*-

"""Datamining Guthub.com.

Usage:
    crawler -l | --language_mine
    crawler -a | --association_mine [--conf=<confidence>] [--sup=<suport>]
    crawler -h | --help

Arguments:
    <confidence>           Confidence precentage
    <suport>               Support precentage

Options:
    -h --help              Displays this help message
    -l --language_mine     Mines Github.com for repos to grenerate a graph
    -a --association_mine  Mines Github.com for users to association
    --conf=<confidence>    Minimum Confidence [default: 80]
    --sup=<suport>         Minimum Support [default: 50]

"""

import configuration
import json
import Queue
import time

from docopt import docopt
import matplotlib.backends.backend_pdf as pdfs
import matplotlib.pyplot as plt
import networkx as nx
import requests

import language2color as ltc
from apriori import run_apriori


contributer_limit = 3

requests.adapters.DEFAULT_RETRIES = 5


def link_to_dict(link):
    """ Web Linking to dictionary.

    Transforms a header Attribute formated as Web Linking (RFC 5988)
    to a dictionary of Relation-types and link-values
    """
    links = link.split(", ")
    rel = {}

    for l in links:
        link_last_idx = l.index(">")
        rel_idx = l.index("rel=") + 5
        rel[l[rel_idx:-1]] = l[1:link_last_idx]

    return rel


def send_get_request_with_retries(url, credentials, cfg,
                                  retries=10, sleep_time=1):
    """Send a HTTP get request and retries if it failes."""
    tries = 0
    while tries <= retries:
        try:
            tries += 1
            return requests.get(url,
                                headers={'User-Agent': cfg.user_agent},
                                auth=credentials)
        except requests.exceptions.ConnectionError:
            time.sleep(sleep_time)
            pass

    raise requests.exceptions.ConnectionError


def get_content(cfg, url):
    """Fetch data from Github.com.

    Based on the url and the configuration in cfg, does it send a get
    request with credentials and if the response uses pagination does
    it follow the links until there are no more.
    If the request is close to the RateLimit specifyed from Github,
    does it wait until the limit resets.
    """
    credentials = requests.auth.HTTPBasicAuth(cfg.git_user, cfg.git_password)
    response = send_get_request_with_retries(url, credentials, cfg)
    if response.status_code == 204:
        raise LookupError("page does not contain any content")
    if response.status_code != 200:
        raise LookupError("Page returned an error.")
    if int(response.headers["X-RateLimit-Remaining"]) < 20:
        # Wait for the reset
        current_time = time.time()
        reset_time = int(response.headers["X-RateLimit-Reset"])
        time.sleep(reset_time - current_time)

    content = json.loads(response.content)

    if 'link' in response.headers:
        link = link_to_dict(response.headers["link"])
        while "next" in link:
            response = send_get_request_with_retries(link['next'],
                                                     credentials,
                                                     cfg)
            content = content + json.loads(response.content)
            link = link_to_dict(response.headers['link'])
    return content


def is_done(user_queue, repo_visited, limit):
    """Check if the algorithm should stop."""
    return user_queue.empty() or len(repo_visited) >= limit


def read_repository(repo, user_queue, repo_visited,
                    queue_limit=1000):
    """Collect the contributors from a repository.

    Extracts the contributors of the repo, and if the number of
    contributors are higher than the contributor limit and the
    user_queue hasn't reach its limit, the users are then added
    to the user_queue
    """
    if repo['id'] not in repo_visited:
        print repo['full_name']
        repo_visited[repo['id']] = repo
        try:
            contributor_url = repo["contributors_url"] + "?per_page=100"
            contributors = get_content(cfg, contributor_url)
            repo["contributors"] = contributors
            if len(contributors) >= contributer_limit and \
               user_queue.qsize() <= queue_limit:
                for contributor in contributors:
                    user_queue.put(contributor)
        except LookupError:
            repo["contributors"] = []


def crawl(cfg):
    """Crawl Github.com for repositories."""
    user_queue = Queue.Queue()

    repo_visited = {}

    for start_repo in cfg.graph_start_repos:
        repo = get_content(cfg, start_repo)
        repo_visited[repo['id']] = repo

    for repo in repo_visited.values():
        users = get_content(cfg, repo["contributors_url"] + "?per_page=100")
        repo["contributors"] = users

        for user in users:
            user_queue.put(user)

    while not is_done(user_queue, repo_visited, cfg.graph_number_of_repos):
        user = user_queue.get()
        print len(repo_visited), user['login'], user_queue.qsize()
        try:
            subscriptions_url = user["subscriptions_url"] + "?per_page=100"
            for user_repo in get_content(cfg, subscriptions_url):
                read_repository(user_repo, user_queue, repo_visited)
        except LookupError:
            pass

    non_fork_repos = filter(lambda repo: not repo['fork'],
                            repo_visited.values())
    return non_fork_repos


def draw_languages(dirty_repos, cfg):
    """Darw programming languages based on the data from the repos.

    Draws a graph where the vertices are languages and the edges
    represent contributers that work in different projects of
    different languages
    """
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

    G.add_nodes_from(languages.keys())

    G.add_edges_from(connections)

    labels = {}
    for lang in languages:
        labels[lang] = "(%d) %s" % (len(languages[lang]), lang)

    node_size = calculate_node_sizes([languages[node] for node in G])

    node_color = [ltc.get_color(node) for node in G]

    edgesize = calculate_edge_sizes([connections[(min(a, b),
                                                  max(a, b))]
                                     for (a, b)
                                     in G.edges_iter()])

    plt.figure(1, figsize=(20, 20))
    nx.draw(G,
            pos=nx.spring_layout(G, iterations=100),
            labels=labels,
            width=edgesize,
            node_size=node_size,
            node_color=node_color,
            linewidths=0.0)

    epoch = time.time()
    save_path = cfg.graph_save_path
    save_path += str(epoch) + "_" + str(cfg.graph_number_of_repos) + ".pdf"

    with pdfs.PdfPages(save_path) as pdf:
        pdf.savefig()

    plt.show()


def calculate_node_sizes(languages, min_size=500, max_size=10000):
    """Calculate the size of the verices of the graph."""
    if not languages:
        return []

    highest = max(len(lang) for lang in languages)
    return [min_size + (max_size - min_size) *
            float(len(lang)) / highest
            for lang in languages]


def calculate_edge_sizes(connections, max_line_size=10):
    """Calculate the thickness of the edges."""
    if not connections:
        return []

    highest = max(connections)
    return [max_line_size
            * float(conn)
            / highest for conn in connections]


def crawl_users(cfg, queue_limit=1000):
    """Crawl Github.com for data about users projects languages.

    The functions crawls though Github.com and looks at peoples
    repos languages
    """
    user_visited = {}
    repo_visited = {}
    user_queue = Queue.Queue()

    # Look at the start repos, and find the users to first look at.
    for repo in cfg.graph_start_repos:
        repo_data = get_content(cfg, repo)
        # Find all contributers and add them to the queue.
        users = get_content(cfg,
                            repo_data["contributors_url"] + "?per_page=100")
        for u in users:
            user_queue.put(u)

    while not is_done(user_queue, user_visited, cfg.graph_number_of_users):
        user = user_queue.get()
        if user['id'] in user_visited:
            continue

        print len(user_visited), user['login'], user_queue.qsize()
        try:
            languages = []
            repos_url = user["repos_url"] + "?per_page=100"
            for user_repo in get_content(cfg, repos_url):
                # Fill up the queue.
                repo_id = user_repo['id']
                if user_queue.qsize() < queue_limit:
                    if(repo_id not in repo_visited):
                        repo_visited[repo_id] = user_repo
                        url = user_repo["contributors_url"] + "?per_page=100"
                        users = get_content(cfg, url)
                        for u in users:
                            if u['id'] not in user_visited:
                                user_queue.put(u)

                # Extract language data.
                lang = user_repo['language']
                if lang is not None and lang not in languages:
                    languages.append(lang)
            user_visited[user['id']] = languages
        except LookupError:
            pass

    return user_visited


def save_users(users, filename):
    """Save the users to a file for association rules."""
    langlist = [','.join(langs) for langs in users.values()]
    text = '\n'.join(langlist)

    file = open(filename, "w")
    file.write(text)
    file.close()


if __name__ == '__main__':
    cfg = configuration.Configuration('config.cfg')

    args = docopt(__doc__)
    if args['--association_mine']:
        min_conf = args['--conf']
        min_sup = args['--sup']

        users = crawl_users(cfg)
        user_filename = 'users.assoc'
        save_users(users, user_filename)
        output_file_items = cfg.graph_save_path + 'apriori_items.txt'
        output_file_rules = cfg.graph_save_path + 'apriori_rules.txt'
        run_apriori(minsup=min_sup,
                    minconf=min_conf,
                    input_file=user_filename,
                    output_file_items=output_file_items,
                    output_file_rules=output_file_rules)
    elif args['--language_mine']:
        repos = crawl(cfg)
        draw_languages(repos, cfg)
