# Authers. Kim Knutzen & Thomas Pedersen

import requests
import json
from pymongo import MongoClient
import configuration
import datetime


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

def row_exists(id):
    doc = next(db.github.find({'id': id}), None)
    return doc != None

if __name__ == '__main__':
    cfg = configuration.Configuration('config.cfg')
    dsn = 'mongodb://{0}:{1}@{2}:{3}/{4}'.format(cfg.db_user, 
                                                 cfg.db_password, 
                                                 cfg.db_host, 
                                                 cfg.db_port, 
                                                 cfg.db_database)
    db = MongoClient(dsn).local

    while datetime.datetime.utcnow() < datetime.datetime(2014, 10, 5):
        mine_github_events(cfg)
