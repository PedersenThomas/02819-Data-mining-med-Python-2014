#Authers. Kim Knutzen & Thomas Pedersen
print('Hello Python World')

import requests
import json
import pprint

content = json.loads(requests.get("https://api.github.com/events", headers={'User-Agent': "kknutzen/1.0"}).content)

#pp = pprint.PrettyPrinter(indent = 1)
#pp.pprint(content)
print json.dumps(content, indent=2)
