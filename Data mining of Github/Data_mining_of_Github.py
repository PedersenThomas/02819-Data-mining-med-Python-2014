#Authers. Kim Knutzen & Thomas Pedersen
print('Hello Python World')

import requests
import json
from pymongo import MongoClient
import datetime

db = MongoClient('mongodb://python:python@www.k-development.dk/local').local

while datetime.datetime.utcnow() < datetime.datetime(2014,10,5):
    print "-------------------------------------------------------"
    content = json.loads(requests.get("https://api.github.com/events", headers={'User-Agent': "kknutzen/1.0"}, auth=requests.auth.HTTPBasicAuth('user', 'pass')).content)
    for data in content:
        obj = next(db.github.find({'id': data['id']}), None)
        if not obj:
            db.github.insert(data)
            print '.'
        else:
            print 'Duuuub'

