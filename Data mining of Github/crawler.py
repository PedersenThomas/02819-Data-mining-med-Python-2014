import configuration
from datetime import datetime
import json
import time
import Queue

#from docopt import docopt
#from pymongo import MongoClient
import requests

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

def crawl(cfg):
    user_queue = Queue.Queue()
    
    repo_visited = list()
    repo_visited.append(get_content(cfg, "https://api.github.com/repos/PedersenThomas/02819-Data-mining-med-Python-2014"))
   
    for user in get_content(cfg, repo_visited[0]["contributors_url"] + "?per_page=100"):
        user_queue.put(user)
    
    i = 0
    while not user_queue.empty():
        user = user_queue.get()
        try:
            for user_repo in get_content(cfg, user["subscriptions_url"] + "?per_page=100"):
                print user_repo["full_name"]
                # check if repo has already been visited (this check does probaly not work if the repo has changed seen it was seen first)
                if not (user_repo in repo_visited):
                    repo_visited.append(user_repo)
                    try:
                        for contributor in get_content(cfg, user_repo["contributors_url"] + "?per_page=100"):
                            user_queue.put(contributor)
                        print "more contributors added"
                    except LookupError:
                        print "No contributors for repo: " + user_repo["full_name"]
                else:
                    print "==== Repo already visited ===="
            i = i + 1
            print i
        except LookupError:
            print "No subscriptions for user: " + user["login"]
    print "fin"

if __name__ == '__main__':
    cfg = configuration.Configuration('config.cfg')
    crawl(cfg)