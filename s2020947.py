#!/usr/bin/python3

# Niels Visscher (s2020947), 2017

import json, requests, sys, re

from sharedcode import *

knownentities = {
	"milk": "wd:Q8495",
	"katsuobushi": "wd:Q113739",
	"Princess Diana": "wd:Q9685"
}

knownprops = {
	"color": "wdt:P462",
	"date of birth": "wdt:P569",
	"country of origin": "wdt:P495",
	"official language": "wdt:P37",
	"place of birth": "wdt:P19",
	"number of households": "wdt:P1538"
}

# Explode function (like in PHP)
def explodeOf(text):
	return re.split(' of ', text)

def cleanSubjectList(data):
	# Remove 'the' and 'a' at beginning of an item
	p = re.compile('(^the\s*|^a\s*)')
	output = []
	for item in data:
		output.append(p.sub('', item))
	# Reconcatenate 'date' and 'birth'
	output2 = str.join(',', output).replace("date,birth", "date of birth").split(",")
	output2 = str.join(',', output2).replace("country,origin", "country of origin").split(",")
	output2 = str.join(',', output2).replace("place,birth", "place of birth").split(",")
	output2 = str.join(',', output2).replace("number,households", "number of households").split(",")
	return output2

# Find an entity. Very important
def findEntity(description):
	try:
		id = knownentities[description]
		return [id]
	except KeyError:
		# Try finding it online
		# Set parameters
		params = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json'}
		url = 'https://wikidata.org/w/api.php'
		params['search'] = description
		# Fetch data
		data = requests.get(url, params=params)
		jsondata = json.loads(data.text)
		# Generate output
		output = []
		for result in jsondata['search']:
			output.append("wd:" + result['id'])
		return output

# Find a property. Also very important
def findProperty(description):
	try:
		id = knownprops[description]
		return [id]
	except KeyError:
		# Try something else
		#debugLog("Niels: Trying to find property " + description)
		# Set parameters
		params = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json', 'type': 'property'}
		url = 'https://wikidata.org/w/api.php'
		params['search'] = description
		# Fetch data
		data = requests.get(url, params=params)
		jsondata = json.loads(data.text)
		# Generate output
		output = []
		for result in jsondata['search']:
			output.append("wdt:" + result['id'])
		return output

# Find the x of a y, assuming that x and y are perfectly formatted for use in sparql
def evaluatePair(x, y, verbose):
	url = 'https://query.wikidata.org/sparql'
	#print("Finding ", x, " of ", y)
	# x is a property, y is an entity
	if verbose:
		query = "SELECT ?answerLabel WHERE { " + y + " " + x + " ?answer . SERVICE wikibase:label { bd:serviceParam wikibase:language \"en\" . } }"
	else:
		query = "SELECT ?answer WHERE { " + y + " " + x + " ?answer . }"
	#print(query)
	data = requests.get(url, params={'query': query, 'format': 'json'})
	jsondata = json.loads(data.text)
	output = []
	for item in jsondata['results']['bindings']:
		for var in item:
			val = item[var]['value']
			val = val.replace("http://www.wikidata.org/entity/", "wd:")
			output.append(val)
	if len(output) > 0:
		return output
	return []

# Recursively resolve the list
def evaluateList(x, y):
	# x and y are lists
	# If all resolved: Return y
	if x == []:
		return y
	# If none resolved yet: Resolve last part of x
	if y == []:
		y = findEntity(x[-1])
		x.pop()
		if y == []:
			return []
		return evaluateList(x, y)
	# Finally: If partially resolved: Resolve last part of x as property of y, and replace y
	props = findProperty(x[-1])
	x.pop()
	if props == []:
		return []
	# We now have a property in prop list, a shortened x, and something in y (also a list)
	# Find 'prop' of 'y' and put it in 'y'
	output = []
	
	for currentprop in props:
		for currenty in y:
			if x == []:
				output = output + evaluatePair(currentprop, currenty, True)
			else:
				output = output + evaluatePair(currentprop, currenty, False)
	if len(x) == 0:
		return output
	else:
		return evaluateList(x, output)

# Parse a single question
def parseWhatis(question):
	# Case: What is ...
	p = re.compile('W(ho|hat) is (.+)\?')
	m = p.match(question)
	if m is None:
		return []
	subject = m.group(2)
	# We now get in 'subject': the name of the queen of England
	subjectlist = explodeOf(subject)
	# We now get: ['the name', 'the queen', 'England']
	subjectlist = cleanSubjectList(subjectlist)
	# We now get: ['name', 'queen', 'England']
	answer = evaluateList(subjectlist, [])
	if answer == []:
		return []
	else:
		return answer


def get_answer_s2020947(question, nlp):
	output = []
	output = output + parseWhatis(question)
	return output
