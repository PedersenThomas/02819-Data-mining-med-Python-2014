"""Datamining Guthub.

Usage: 
    mine_github mine --until <date>
    mine_github preprocess
    mine_github -h | --help

Arguments:
    <date>          The desired date to mine until 'yyyy-mm-dd'

Options:
    -h --help       Show help message 
    --until <date>  Specify stopping date for mining
  
"""

import requests
import json
from pymongo import MongoClient
import configuration
from datetime import datetime
from docopt import docopt


def mine_github_events(cfg):
    credentials = requests.auth.HTTPBasicAuth(cfg.git_user, cfg.git_password)
    response = requests.get("https://api.github.com/events",
                            headers={'User-Agent': cfg.user_agent},
                            auth=credentials)

    events = json.loads(response.content)
    for event in events:
        obj = next(db.github.find({'id': event['id']}), None)
        if not obj:
            db.github.insert(event)

def preprocess(dsn):
    db = MongoClient(dsn).local
    
    #
    # How to iterate over large datasets
    # https://groups.google.com/forum/#!topic/mongodb-user/YQGOPZjRtlY
    # http://docs.mongodb.org/manual/tutorial/create-tailable-cursor/
    #
    for event in db.github.find( timeout=False ):
        name = event["repo"]["name"]
        type = event["type"]
        object_id = event["_id"]

        #Lookup existing repo
        repo = next(db.repos.find({'name': name}), None)
        if not repo:
            #insert repo 
            repo = {"name" : name, "event" : {type : [object_id]}}
            db.repos.insert(repo)
        else:
            #Update the existing by appending the event
            if repo["event"].has_key(type):
                if not object_id in repo["event"][type]:
                    repo["event"][type].append(object_id)
            else:
                repo["event"][type] = [object_id]
            db.repos.update({'_id':repo["_id"]}, 
                            {"$set": {"event" : repo["event"]}}, upsert=False)
            

def row_exists(id):
    doc = next(db.github.find({'id': id}), None)
    return doc != None


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = configuration.Configuration('config.cfg')
    dsn = 'mongodb://{0}:{1}@{2}:{3}/{4}'.format(cfg.db_user, 
                                                 cfg.db_password, 
                                                 cfg.db_host, 
                                                 cfg.db_port, 
                                                 cfg.db_database)

    if args["mine"]:
        until = datetime.strptime(args["<until>"], "%Y-%m-%d")
        db = MongoClient(dsn).local

        while datetime.utcnow() < until:
            mine_github_events(cfg)
    
    elif args["preprocess"]:
        preprocess(dsn)

    else:
        print "Command not recognized"
