"""Datamining Guthub.

Usage: mine_github <until>

Options: --until  Mines until specified date as 'yyyy-mm-dd'
  
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


def row_exists(id):
    doc = next(db.github.find({'id': id}), None)
    return doc != None


if __name__ == '__main__':
    args = docopt(__doc__)
    until = datetime.strptime(args["<until>"], "%Y-%m-%d")
    cfg = configuration.Configuration('config.cfg')
    dsn = 'mongodb://{0}:{1}@{2}:{3}/{4}'.format(cfg.db_user, 
                                                 cfg.db_password, 
                                                 cfg.db_host, 
                                                 cfg.db_port, 
                                                 cfg.db_database)
    db = MongoClient(dsn).local

    while datetime.utcnow() < until:
        mine_github_events(cfg)