#Authers. Kim Knutzen & Thomas Pedersen
print('Hello Python World')

import requests
import json
import pprint
from pymongo import MongoClient

db = MongoClient('mongodb://python:python@www.k-development.dk/local').local

for _ in range(20):
    print "-------------------------------------------------------"
    content = json.loads(requests.get("https://api.github.com/events", headers={'User-Agent': "kknutzen/1.0"}, auth=requests.auth.HTTPBasicAuth('user', 'password')).content)
    for data in content:
        obj = next(db.github.find({'id': data['id']}), None)
        if not obj:
            db.github.insert(data)
            print '.'
        else:
            print 'Duuuub'

