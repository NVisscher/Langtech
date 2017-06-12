#!/usr/bin/python3
import requests
import re
import string
import mmap
import time

debugMode = True

def debugLog(message):
	if debugMode:
		print("[Debug]", message)
	pass

#Read the whole file to a dictionary
def init_anchor_dict():
  file = open('anchor_texts', 'r')
  m = mmap.mmap(file.fileno(), 0, access = mmap.ACCESS_READ)
  pattern = re.compile(rb"^(.*)\t(<.*>)\t([0-9]+)", re.MULTILINE)
  anchor_dict = {}
  for match in pattern.findall(m):
    key = str(match[0], 'utf-8')
    url = str(match[1], 'utf-8')
    count = int(str(match[2], 'utf-8'))
    if key not in anchor_dict:
      anchor_dict[key] = []
    anchor_dict[key].append((url, count))
  return anchor_dict

#Pick the best entities from the anchor dict
def entities_from_anchor_dict(key, anchor_dict):
  if key not in anchor_dict:
    return []
  occurences = anchor_dict[key]
  total = 0
  for word, cnt in occurences:
    total += cnt
  avg = int(total/len(occurences))
  url = 'https://query.wikidata.org/sparql'
  ret = []
  for word, cnt in occurences:
    if cnt >= avg:
      query = 'SELECT ?e WHERE {'+word+' schema:about ?e .}'
      result = requests.get(url,params={'query': query, 'format': 'json'}).json()['results']['bindings']
      for item in result:
        ret.append(item['e']['value'][31:])
  return ret

