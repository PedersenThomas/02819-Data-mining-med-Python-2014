import configuration
from datetime import datetime
import json
import time
import Queue

#from docopt import docopt
#from pymongo import MongoClient
import requests
import matplotlib.pyplot as plt
import networkx as nx

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
    if response.headers["X-RateLimit-Remaining"] == 0:
        # Wait
        current_time = time.time()
        reset_time = response.headers["X-RateLimit-Reset"]
        print "RateLimit exceeded Wait seconds: " + (reset_time - current_time)
        time.sleep(reset_time - current_time)

    content = json.loads(response.content)
    
    if 'link' in response.headers:
        link = link_to_dict(response.headers["link"])
        while "next" in link:
            print "next page " + link['next']
            response = requests.get(link['next'],
                                    headers={'User-Agent': cfg.user_agent},
                                    auth=credentials)
            content = content + json.loads(response.content)
            link = link_to_dict(response.headers['link'])
    return content

def read_repository(user_repo, user_queue, repo_visited):
    print user_repo["full_name"]
    # check if repo has already been visited (this check does probaly not work if the repo has changed seen it was seen first)
    if not (user_repo in repo_visited):
        repo_visited.append(user_repo)
        try:
            contributors = get_content(cfg, user_repo["contributors_url"] + "?per_page=100")
            user_repo["contributors"] = contributors
            if len(contributors) >= 10:
                for contributor in contributors:
                    user_queue.put(contributor)
        except LookupError:
            print "No contributors for repo: " + user_repo["full_name"]
    else:
        print "==== Repo already visited ===="

def is_done(user_queue, repo_visited):
    return user_queue.empty() or len(repo_visited) >= 100

def crawl(cfg):
    start_repo = "https://api.github.com/repos/Microsoft/TypeScript"

    user_queue = Queue.Queue()
    G = nx.Graph()

    repo_visited = list()
    repo_visited.append(get_content(cfg, start_repo))
    
    users = get_content(cfg, repo_visited[0]["contributors_url"] + "?per_page=100")
    repo_visited[0]["contributors"] = users
    for user in users:
        user_queue.put(user)
    

    while not is_done(user_queue, repo_visited):
        user = user_queue.get()
        print "===== " + user["login"]
        try:
            for user_repo in get_content(cfg, user["subscriptions_url"] + "?per_page=100"):
                read_repository(user_repo, user_queue, repo_visited)
        except LookupError:
            print "No subscriptions for user: " + user["login"]
        print "===== " + str(len(repo_visited))
    G.add_nodes_from([repo["full_name"] for repo in repo_visited])
    labels = {repo["full_name"]: repo["name"] for repo in repo_visited}
    
    for a in repo_visited:
        for b in repo_visited:
            if a != b:
                a_users = [user["login"] for user in a["contributors"]]
                b_users = [user["login"] for user in b["contributors"]]
                shared_users = set(a_users).intersection(b_users)
                if len(shared_users) > 5:
                    G.add_edge(a["full_name"], b["full_name"])
    
    node_size = [len(repo['contributors']) for repo in repo_visited]
    nx.draw(G, layout=nx.spring_layout(G), labels=labels, node_size = node_size)
    plt.show()


if __name__ == '__main__':
    cfg = configuration.Configuration('config.cfg')
    crawl(cfg)