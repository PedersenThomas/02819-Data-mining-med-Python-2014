"""Datamining Guthub.

Usage:
    mine_github mine --until <date>
    mine_github preprocess
    mine_github proc_user
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
    cnt = 0
    for event in db.github.find(timeout=False):
        name = event["repo"]["name"]
        type = event["type"]
        object_id = event["_id"]

        # Lookup existing repo
        repo = next(db.repos.find({'name': name}), None)
        if not repo:
            # insert repo
            repo = {"name": name, "event": {type: [object_id]}}
            db.repos.insert(repo)
        else:
            # Update the existing by appending the event
            if type in repo["event"]:
                if object_id not in repo["event"][type]:
                    repo["event"][type].append(object_id)
            else:
                repo["event"][type] = [object_id]
            db.repos.update({'_id': repo["_id"]},
                            {"$set": {"event": repo["event"]}}, upsert=False)
        cnt += 1
        if cnt % 1000 == 0:
            print "Number of events processed: {0}".format(cnt)
            print "The last object_id was: {0}".format(object_id)

def preprocess_users(dsn):
    db = MongoClient(dsn).local

    #
    # How to iterate over large datasets
    # https://groups.google.com/forum/#!topic/mongodb-user/YQGOPZjRtlY
    # http://docs.mongodb.org/manual/tutorial/create-tailable-cursor/
    #
    cnt = 0
    for event in db.github.find(timeout=False):
        name = event["actor"]["login"]
        id = event["actor"]["id"]
        reponame = event["repo"]["name"]
        type = event["type"]
        object_id = event["_id"]

        # Lookup existing user
        user = next(db.users.find({'id': id}), None)
        if not user:
            # insert user
            user = {"id": id, "name": name, "repository": [ { "name": reponame, 
                                                              "events": {type: [object_id]}
                                                             }]
                    }
            db.users.insert(user)
        else:
            # Update the existing by appending the event
            arr = [x for x in user["repository"] if x["name"] == reponame]
            if arr:
                if type in arr[0]['events']:
                    if object_id not in arr[0]['events'][type]:
                        arr[0]['events'][type].append(object_id)
                else:
                    arr[0]['events'][type] = [object_id]
            else:
                user["repository"].append({"name": reponame, "events": {type: [object_id]}})
            db.users.update({'_id': user["_id"]},
                            {"$set": {"repository": user["repository"]}}, upsert=False)
        cnt += 1
        if cnt % 1000 == 0:
            print "Number of events processed: {0}".format(cnt)
            print "The last object_id was: {0}".format(object_id)


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

    elif args["proc_user"]:
        preprocess_users(dsn)

    else:
        print "Command not recognized"
