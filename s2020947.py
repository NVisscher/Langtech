#!/usr/bin/python3

# Language Technology Practical, Assignment 3
# Niels Visscher (s2020947), 2017

import json, requests, sys, re

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

# Function that displays examples
def showExamples():
	print('''Example questions:
What is the date of birth of Richard Stallman?
What is the official language of the country of origin of katsuobushi?
What is the color of milk?
What is the use of a plate?
What is the gender of Caitlyn Jenner?
Who is the president of the United States?
Who is the prime minister of the Netherlands?
What is the population of the place of birth of the mayor of Amsterdam?
What is the number of households of Emmen?
Who is the father of the mother of the father of Princess Diana?
---''')
	pass

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
		#print("Finding entity " + description)
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
		#print("Trying to find property " + description)
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
		#print(output)
		return output
	return []

# Recursively resolve the list
def evaluateList(x, y):
	# x and y are lists
	# If all resolved: Return y
	if x == []:
		return [y]
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
def parseQuestion(question):
	# Case: What is ...
	p = re.compile('W(ho|hat) is (.+)\?')
	m = p.match(question)
	if m:
		subject = m.group(2)
		# We now get in 'subject': the name of the queen of England
		subjectlist = explodeOf(subject)
		# We now get: ['the name', 'the queen', 'England']
		subjectlist = cleanSubjectList(subjectlist)
		# We now get: ['name', 'queen', 'England']
		answer = evaluateList(subjectlist, [])
		if answer == []:
			print("No answer could be found")
		else:
			for answeritem in answer:
				if answeritem != []:
					print(answeritem)
	else:
		print("Question could not be understood")
	pass

# Show examples
showExamples()

# Read ten questions from standard input
while True:
	try:
		question = input("Question: ")
		parseQuestion(question)
	except EOFError:
		break
	pass
