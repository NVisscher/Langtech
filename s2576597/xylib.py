#!/usr/bin/python3
import sys
import requests
import re
import string
import mmap
import time
from lxml import html
from learnparse import parse_question

#Use wikidata search engine for properties
def get_scraper_props(name):
  page = requests.get('https://www.wikidata.org/w/index.php?search='+name+'&title=Special:Search&profile=advanced&fulltext=1&ns120=1&searchToken=4rjaotw3j18mh99lrqle4lkw2')
  tree = html.fromstring(page.content)
  props = tree.xpath('//*[@id="mw-content-text"]/div[2]/ul/li/div[1]/a/span/span[2]/text()')
  translator = str.maketrans('', '', string.punctuation)
  retprops = []
  for prop in props:
    prop = prop.translate(translator)
    retprops.append(prop)
  return retprops

#Read the whole file to a dictionary
def init_anchor_dict():
  file = open('../anchor_texts', 'r')
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
def entities_from_anchor_dict(key):
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

#Use wikidata API to find properties and entities
def get_uri(name, isProperty):
  url = 'https://www.wikidata.org/w/api.php'
  params = {'action':'wbsearchentities',
    'language':'en',
    'format':'json'}
  if isProperty:
    params['type'] = 'property'
  params['search'] = name
  json = requests.get(url,params=params).json()
  ret = []
  for result in json['search']:
    ret.append(result['id'])
  return ret

#Create query for the combination of one entity and one property
def create_query(entity, prop):
  query = '''
  SELECT ?answer ?answerLabel WHERE {
    wd:'''+entity+''' wdt:'''+prop+''' ?answer .
    SERVICE wikibase:label {
      bd:serviceParam wikibase:language "en" .
    }
  }'''
  return query

#Fire one query and return possible answers
def fire_query(query):
  url = 'https://query.wikidata.org/sparql'
  data = requests.get(url,params={'query': query, 'format': 'json'}).json()
  answers = []
  for item in data['results']['bindings']:
    answers.append(item['answerLabel']['value'])
  return answers

#remove stupid identifiers:
def is_bad_property(prop):
  badProperties = ['P227', 'P213', 'P217']
  if prop in badProperties:
    return True
  return False
    
#Try all combinations of a list of properties and a list of entities
def fire_queries(entities, properties):
  for entity in entities:
    for prop in properties:
      if is_bad_property(prop):
        continue
      answers = fire_query(create_query(entity, prop))
      if answers:
        return answers
  return []

def get_entities(entityString):
  entities = get_uri(entityString,False) #Get uri's for the entity from wikidata API
  extraents = entities_from_anchor_dict(entityString)#Get extra entity uris from anchor texts
  for ent in extraents:
    if ent not in entities:
      entities.append(ent)
  return entities

def get_properties(propertyString):
  properties = get_uri(propertyString,True) #Get uri's for the property from wikidata API
  extraprops = get_scraper_props(propertyString)
  for prop in extraprops:
    if prop not in properties:
      properties.append(prop)
  return properties


def create_and_fire_query(line, nlp):
  entsAndProps = parse_question(line, nlp)
  entStrings = entsAndProps[0]
  propStrings = entsAndProps[1]
  if not entStrings or not propStrings:
    return []
  for entityString in entStrings:
    entities = get_entities(entityString)
    for propertyString in propStrings:
      if propertyString == entityString:
        continue
      properties = get_properties(propertyString)
      answers = fire_queries(entities, properties) #Try all combination(start with best)
      if answers:
        return answers
      elif ' ' in propertyString:
        tempprop = propertyString.split(' ')[len(propertyString.split(' '))-1]
        properties = get_properties(tempprop)
        answers = fire_queries(entities, properties) #Try all combination(start with best)
        if answers:
          return answers
    if ' ' in entityString: # Try last part of composed nouns
      tempent = entityString.split(' ')[len(entityString.split(' '))-1]
      entities = get_entities(tempent)
      for propertyString in propStrings:
        if propertyString == entityString:
          continue
        properties = get_properties(propertyString)
        answers = fire_queries(entities, properties) #Try all combination(start with best)
        if answers:
          return answers
  return []

print("\nReading anchor_texts to dictionary(about 20 seconds)\nPlease wait...")
start = time.time()
anchor_dict = {}#init_anchor_dict()
print("Completed in " + str(time.time()-start) + " seconds.\n")
