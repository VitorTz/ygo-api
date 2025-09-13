import requests
import json


with open("res/data.json") as file:
    data = json.load(file)


keys = set()

archetypes = set()

for card in data:
    for k in card.keys():
        if k == 'archetype':
            archetypes.add(card['archetype'])


for a in sorted([x for x in archetypes]):
    print(a)