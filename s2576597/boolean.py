import requests
from learnparse import getKey, makeTree, treeToArray, getArrayOfNounsAndVerbs, skip, changeText
from xylib import get_entities, get_properties

def getGoodTokens(line, nlp):
  array = treeToArray(makeTree(line, nlp))
  nounsandverbs = getArrayOfNounsAndVerbs(line, nlp)
  tokens = []
  for token in array:
    if changeText(token).text in nounsandverbs and not skip(changeText(token).text) and not token.text == 'considered' and not token.text == 'contain':
      tokens.append(changeText(token))
  return tokens

def queryEntEnt(entList1, entList2):
  for ent1 in entList1:
    for ent2 in entList2:
      query = "ASK {wd:"+ent1+" ?free wd:"+ent2+" .}"
      url = 'https://query.wikidata.org/sparql'
      data = requests.get(url,params={'query': query, 'format': 'json'}).json()
      if data['boolean']:
        return True

def queryEntProp(entList1, entList2):
  for ent1 in entList1:
    for ent2 in entList2:
      query = "ASK {wd:"+ent1+" wdt:"+ent2+" ?free .}"
      url = 'https://query.wikidata.org/sparql'
      data = requests.get(url,params={'query': query, 'format': 'json'}).json()
      if data['boolean']:
        return True

def solveBooleanQuestion(line, nlp):
  tokens = getGoodTokens(line, nlp)
  #Check if there are no conjuctions
  for token in tokens:
    if token.conj:
      return solveConjunctedQuestion(tokens)
  #Otherwise first test entity ? entity
  string = ''
  for token in tokens:
    string += token.text + ' | '
  #print (string)
  if len(tokens) > 3:#Lot quicker maar mischien niet optimaal
    return ['Yes']
  for ent1 in tokens:
    entList1 = get_entities(ent1.text)
    for ent2 in tokens:
      if(ent1.text == ent2.text):
        continue
      if queryEntEnt(entList1, get_entities(ent2.text)):
        return ['Yes']
      if queryEntProp(entList1, get_properties(ent2.text)):
        return ['Yes']
  #And then test entity property
  return ['No']

def solveConjunctedQuestion(tokens):
  otherEnts = []
  lastEnts = []
  isOr = False
  for token in tokens:
    if token.conj and ' or ' in token.text:
      lastEnts = token.text.split(' or ')
      isOr = True
    elif token.conj and ' and ' in token.text:
      lastEnts = token.text.split(' and ')
    else:
      otherEnts.append(token.text)
  if len(lastEnts) < 2:
    return ["Yes"]
  #print(isOr, " lastEnts:", lastEnts, ' otherEnts:',otherEnts)
  if isOr:
    for otherent in otherEnts:
      ret = ''
      ent1 = get_entities(otherent)
      if queryEntEnt(ent1, get_entities(lastEnts[0])):
        ret = lastEnts[0]
      if queryEntEnt(ent1, get_entities(lastEnts[1])):
        if ret == '':
          ret = lastEnts[1]
        else:
          ret = 'both ' + lastEnts[0] + ' and ' + lastEnts[1]
      if not ret == '':
        return [ret]
    return [lastEnts[0]]
  else:# not or but and
    for otherent in otherEnts:
      ent1 = get_entities(otherent)
      if queryEntEnt(ent1, get_entities(lastEnts[0])) and queryEntEnt(ent1, get_entities(lastEnts[1])):
        return ["Yes"]
  return ["No"]
