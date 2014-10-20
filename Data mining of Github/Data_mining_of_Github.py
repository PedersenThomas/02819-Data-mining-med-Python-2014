# Authers. Kim Knutzen & Thomas Pedersen
print('Hello Python World')

import ConfigParser
import requests
import json
from pymongo import MongoClient
import datetime

def read_config():
    config = ConfigParser.ConfigParser({'port':'27017'})
    config.read('config.cfg')

    sec_Database = 'Database'
    db_user = config.get(sec_Database, 'user')
    db_pw = config.get(sec_Database, 'password')
    db_host = config.get(sec_Database, 'host')
    db_port = config.get(sec_Database, 'port')
    database = config.get(sec_Database, 'database')

    sec_Github = 'Github'
    git_user = config.get(sec_Github, 'user')
    git_pw = config.get(sec_Github, 'password')
    git_useragent = config.get(sec_Github, 'user-agent')



def mine_github_events(while_predicate):
    response = requests.get("https://api.github.com/events",
                            headers={'User-Agent': git_useragent},
                            auth=requests.auth.HTTPBasicAuth(git_user, git_pw))
    events = json.loads(response.content)
    for event in events:
        obj = next(db.github.find({'id': event['id']}), None)
        if not obj:
            db.github.insert(event)

def row_exists(id):
    doc = next(db.github.find({'id': id}), None)
    return doc != None

if __name__ == '__main__':
    read_config()
    dsn = 'mongodb://{0}:{1}@{2}:{3}/{4}'.format(db_user, 
                                                 db_pw, 
                                                 db_host, 
                                                 db_port, 
                                                 database)
    db = MongoClient(dsn).local

    while datetime.datetime.utcnow() < datetime.datetime(2014, 10, 5):
        mine_github_events()