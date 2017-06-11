from xylib import get_entities
from boolean import getGoodTokens
import requests

def get_description(ent):
  query = """SELECT ?itemDescription WHERE {
  wd:""" + ent + """ schema:description ?itemDescription.
  FILTER(LANG(?itemDescription) = "en")
}"""
  url = 'https://query.wikidata.org/sparql'
  data = requests.get(url,params={'query': query, 'format': 'json'}).json()
  description = None
  try:
    description = data["results"]["bindings"][0]["itemDescription"]["value"]
  except:
    pass
  if description == 'Wikipedia disambiguation page':
    return None
  return description

def solveWhatIsQuestion(line, nlp):
  tokens = getGoodTokens(line, nlp)
  text = tokens[len(tokens)-1].text
  entities = get_entities(text)
  for ent in entities:
    descr = get_description(ent)
    if descr:
      return [descr]
  return []
  
