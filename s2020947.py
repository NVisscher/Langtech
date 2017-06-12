#!/usr/bin/python3

# Niels Visscher (s2020947), 2017

import json, requests, sys, re

from sharedcode import *

anchordict = {}

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

# Pattern format: (regex, [list of positions, in order], [evaluation prefix])
patterns = [
	('What (.+) (does|do|can) (.+) have?', [0, 2], []),
	('When was (.+) born?', [0], ["date of birth"]),
	('W(ho|hat)( is| are|\'s) (.+)\?', [2], []),
	('W(ho|hat)( is| are|\'s) the (.+) in (.+)\?', [2, 3], []),
	('What is (a|an) (.+)\?', [1], ["subclass of"]),
	('What is (\S+)\?', [0], ["instance of"]),
	('In (what|which) (.+) (do|does) (.+) (come|exist)?', [1, 3], []),
	('(Where|What country|What place) (do|does) (.+) (originate|come) from?', [2], ["country of origin"]),
	('Wh(at|ich) (.+)was (.+) named after?', [2], ["named after"]),
	('After wh(at|ich|om) (.+)was (.+) named?', [2], ["named after"]),
	('What( is|\'s) (.+) used for?', [1], ["use"]),
	('What (do|does) (.+) consist of?', [1], ["has part"]),
	('(What|Which) (.+) is (also known|known) as (.+)?', [3], ["known as"]),
	('What kind of (.+) is (.+)?', [1], ["subclass of"])
	]

knownagents = {
	"invent": "inventor"
	}

howmanyhaspatterns = [
	'How many (.+) (does|do) (.+) have\?',
	'How many (.+) are there (in|at|with) (.+)\?',
	'What is the number of (.+) (in|at|of) (.+)\?']

# Explode function (like in PHP)
def explodeOf(text):
	return re.split(' of ', text)

def cleanSubjectList(data):
	# Remove 'the' and 'a' at beginning of an item
	p = re.compile('(^the \s*|^a(|n) \s*)')
	output = []
	for item in data:
		output.append(p.sub('', item))
	# Reconcatenate 'date' and 'birth'
	output2 = str.join(',', output).replace("date,birth", "date of birth").split(",")
	output2 = str.join(',', output2).replace("country,origin", "country of origin").split(",")
	output2 = str.join(',', output2).replace("place,birth", "place of birth").split(",")
	output2 = str.join(',', output2).replace("number,households", "number of households").split(",")
	output2 = str.join(',', output2).replace("number,employees", "number of employees").split(",")
	return output2

# Very complicated function to turn "found" into "founder"
def findAgent(lemma):
	if lemma in knownagents:
		return knownagents[lemma]
	# Unknown agent. Try the generic way.
	if lemma[-1] == 'e':
		return lemma + "r"
	return lemma + "er"

# Find an entity. Very important
def findEntity(description):
	if description == '':
		return []
	try:
		id = knownentities[description]
		if id != "":
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
		if output:
			return output
		output = entities_from_anchor_dict(description, anchordict)
		return output

# Find a property. Also very important
def findProperty(description):
	if description == '':
		return []
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
	# Special case: Y has been resolved, and X is "number". REPLACED.
	#if x == ["number"]:
	#	return [str(len(y))]
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

# Parse a what-is question. Deprecated and replaced by generic pattern.
def parseWhatis(question, doc):
	# Case: What is ...
	p = re.compile('W(ho|hat) (is|are) (.+)\?')
	m = p.findall(question)
	if len(m) < 1:
		return []
	# At least 3 words have to be matched
	if len(re.split(" ", m[0][2])) < 3:
		return []
	# Convert to lemma forms
	subject = str.join("", doc[2:-1].lemma_)
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


def parseWhodid(question, doc):
	p = re.compile('W(ho|hat) (.+)\?')
	m = p.match(question)
	if m is None:
		return []
	if doc[1].pos_ != 'VERB' or doc[1].lemma_ == 'be' or doc[1].lemma_ == 'do':
		return []
	# Who Xed Y? => Who is the X-or of Y?
	y = explodeOf(str.join("", doc[2:-1].lemma_))
	subjectlist = [findAgent(str(doc[1].lemma_))] + cleanSubjectList(y)
	answer = evaluateList(subjectlist, [])
	return answer

def parseImperative(question, doc):
	if doc[0].pos_ != 'VERB' or str(doc[0]).lower() != doc[0].lemma_:
		return []
	subjectlist = cleanSubjectList(explodeOf(str.join("", doc[1:].lemma_)))
	#print("Imp:", subjectlist)
	answer = evaluateList(subjectlist, [])
	return answer

def parseHowManyHave(question, doc):
	# Not Implemented Yet
	answers = []
	for pattern in howmanyhaspatterns:
		p = re.compile(pattern)
		m = p.findall(question)
		for match in m:
			x = match[0] # Example: employees
			y = cleanSubjectList(explodeOf(match[2])) # Example: Burger King
			# Try "X" of "Y" and hope to find a number
			answer = evaluateList([x] + y, [])
			for item in answer:
				try:
					val = int(item)
					answers.append(val)
				except ValueError:
					pass
			# Try "Number of X" of "Y" and hope to find a number
			x = "number of " + match[0]
			answer = evaluateList([x] + y, [])
			for item in answer:
				try:
					val = int(item)
					answers.append(val)
				except ValueError:
					pass
			# Try the lemma of X with Y, and count the results
			x = findLemmaForms(doc, match[0])
			answer = evaluateList([x] + y, [])
			if len(answer) > 0:
				answers.append(len(list(set(answer))))
	if answers == []:
		return []
	return [str(max(answers))]

# Retrieves lemma forms from the parsed document, and replaces them in the 'raw' input
def findLemmaForms(doc, raw):
	output = []
	words = re.split(' ', raw)
	for word in words:
		for docitem in doc:
			if str(docitem) == word:
				output.append(docitem.lemma_)
				break
	return " ".join(output)

def parseGeneric(question, doc):
	answers = []
	for pattern in patterns:
		(repattern, positions, prefix) = pattern
		p = re.compile(repattern)
		m = p.findall(question)
		for match in m:
			# Populate subject list in order
			subjectlist = []
			for pos in positions:
				chunk = ""
				# Workaround for quirk in Python3 regex
				if type(match) is tuple:
					chunk = match[pos]
				else:
					chunk = match
				chunk = findLemmaForms(doc, chunk)
				subjectlist = subjectlist + explodeOf(chunk)
			subjectlist = prefix + cleanSubjectList(subjectlist)
			answers = answers + evaluateList(subjectlist, [])
	return answers


def get_answer_s2020947(question, nlp, anchor_dict):
	nonewline = question.replace('\n', '')
	doc = nlp(nonewline)
	anchordict = anchor_dict
	output = []
	#output = output + parseWhatis(question, doc)
	output = output + parseWhodid(question, doc)
	output = output + parseImperative(question, doc)
	output = output + parseHowManyHave(question, doc)
	output = output + parseGeneric(question, doc)
	return output
