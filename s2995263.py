#!/usr/bin/python3

import sys
import requests
import re
import json
import spacy
#from sharedcode import*

def get_answer_s2995263(question, nlp):
	nonewline = question.replace('\n', '')
	result = nlp(nonewline)
	output =[]
	output.extend(get_answer(result))
	return output
	
	
def get_answer(result):
	[prop, ent, value] = findItems(result) #extract the useful words from the question
	if [prop, ent, value]== [0,0,0]:
		return []
	if value !=None:
		answer = yesnoQuery(prop, ent, value)
		if answer == True:
			return "yes"
		else:
			return "no"
	elif prop!=None:
		answer = createAndFireQuery(prop, ent)
	else:
		answer = descriptionQuery(ent)
	if not answer:
		return []
	else:
		lijst=[]
		for item in answer:
			lijst.append(item)
		return lijst
	

def main(argv):

	printExampleQueries();
	nlp = spacy.load('en_default')
	for line in sys.stdin:
		if line == "\n" or line == None:
			print("You stopped.")
			return	
		result = nlp(line)
		[prop, ent, value] = findItems(result) #extract the useful words from the question
		if [prop, ent, value]== [0,0,0]:
			continue
		if value !=None:
			answer = yesnoQuery(prop, ent, value)
			if answer == True:
				print("yes")
			else:
				print("no")
		else: 
			if prop != None:
				answer = createAndFireQuery(prop, ent)
			elif ent!=None:
				answer = descriptionQuery(ent)
				if not answer:
					print("cannot find description")
					continue
			if not answer:
				print("Either I did not understand your question or the answer is not known by Wikidata. Sorry.")
			else:
				for item in answer:
					print(item)
					
knownentities={
	"male": "Q6581097",
	"female": "Q6581072"
}

knownproperties=["instance of","subclass of"]
containproperties=["has part", "materials used"]

def descriptionQuery(ent):
	outcome = []
	uri = searchWithAnchorText(ent)	#Find the uri of the entity using Wikipedia anchor text
	if uri == 'empty':
		print("We cannot find \'" + ent +"\', so:")
		return []
	Qent = []
	for x in uri:
		Qent.append(searchEntity(x)) #Find the Q number of the uri found above
	for ent in Qent:
			wdQent = 'wd:'+ent
			url = 'https://query.wikidata.org/sparql'
			query =	'''SELECT ?answerDescription WHERE {
						BIND(''' + wdQent +  ''' AS ?answer) .
						SERVICE wikibase:label {
							bd:serviceParam wikibase:language "en" .
						}
					}'''
			data = requests.get(url,
				params={'query': query, 'format': 'json'}).json()

			for item in data['results']['bindings']:
				for var in item :
					if item[var]['type'] != 'uri':
						if item[var]['value'] not in outcome:
							outcome.append(item[var]['value'])
			if outcome:
				return outcome
	return outcome
	
def createAndFireQuery(prop, ent):
	outcome =[]
	Qprop = []
	Qprop.extend(searchIdProp(prop)) #Find the Q number of the property
	#Qent = str(searchIdEnt(ent)) #Only need this when using wikidataAPI instead of wikipedia anchor texts

	uri = searchWithAnchorText(ent)	#Find the uri of the entity using Wikipedia anchor text
	if uri == 'empty':
		print("We cannot find \'" + ent +"\', so:")
		return []
	Qent = []
	for x in uri:
		Qent.append(searchEntity(x)) #Find the Q number of the uri found above
	for ent in Qent:
		for prop in Qprop:
			print(prop, Qprop)
			wdQent = 'wd:'+ent
			wdtQprop = 'wdt:'+prop

			url = 'https://query.wikidata.org/sparql'
			query =	'''SELECT ?answer ?answerLabel  WHERE {
						''' + wdQent + ' ' + wdtQprop + ''' ?answer .
						SERVICE wikibase:label {
							bd:serviceParam wikibase:language "en" .
						}
					}'''
			data = requests.get(url,
				params={'query': query, 'format': 'json'}).json()

			for item in data['results']['bindings']:
				for var in item :
					if item[var]['type'] != 'uri':
						if item[var]['value'] not in outcome:
							outcome.append(item[var]['value'])
			if outcome:
				return outcome
	return outcome

def entityList(ent):
	ret = []
	if ent in knownentities:
		ret.append(knownentities[ent])
	#API
	ret.append(searchIdEnt(ent))
	#Anchor texts
	uriEnt = searchWithAnchorText(ent)	#Find the uri of the entity using Wikipedia anchor text
	for x in uriEnt:
		print('x = ', x)
		ret.append(searchEntity(x)) #Find the Q number of the uri found above
	if not ret:
		print("We cannot find \'" + ent)
		return []
	return ret

#Function to create and fire a yes/no query
def yesnoQuery(prop, ent, value):
	Qprop = []
	Qent = entityList(ent)
	Qval = entityList(value)
	outcome = []
	Qprop.extend(searchIdProp(prop)) #Find the Q number of the property 
	if prop == None:
		for x in knownproperties:
			Qprop.extend(searchIdProp(x))
	if prop == 'contain':
		for x in containproperties:
			Qprop.extend(searchIdProp(x))

			
	print('asking query :', Qent, Qval, Qprop)
	for ent in Qent:
		for val in Qval:
			for prop in Qprop:
				wdQval = 'wd:' + val
				wdQent = 'wd:'+ ent
				wdtQprop = 'wdt:'+prop
				url = 'https://query.wikidata.org/sparql'
				query = '''ASK {''' +wdQent + ' ' + '?free' + ' ' + wdQval+ '''}'''
				data = requests.get(url,
					params={'query': query, 'format': 'json'}).json()
				outcome = data['boolean']
				#print(query, outcome)
				if outcome:
					return outcome
	return outcome


#Function to find the wikipedia URI using anchor texts given the name of the entity. 
def searchWithAnchorText(ent):
	frequencies =[] #integer array to store freqs
	uris = [] #string array to store URIs
	with open('anchor_texts', 'r', encoding='utf-8') as inF:
		for line in inF:
			if line.startswith(ent+"\t"):
				line = line.rstrip() # removes newline
				x=re.split(r'\t+',line) #string array with text, uri and freq
				#Store the frequency and URI:
				uris.append(x[1]) 
				frequencies.append(int(x[2])) 
	if not frequencies: #the word is not found in the anchor texts
		return []
#	freq = max(frequencies) #Find the most common meaning
#	max_index = frequencies.index(freq)	
#	uri = uris[max_index
	output = []
	for i in range(0,5):
		if uris:
			freq = max(frequencies) #Find the most common meaning
			max_index = frequencies.index(freq)	
			output.append(uris[max_index])
			uris.remove(uris[max_index])
			frequencies.remove(max(frequencies))
	return output

#Function to find the Q-number given the wikipedia URI:
def searchEntity(uri):
	url = 'https://query.wikidata.org/sparql'
	query =	'''SELECT ?e WHERE {
				''' + uri + ' ' + ''' schema:about ?e .
			}'''
	params={'query': query, 'format': 'json'}

	data = requests.get(url, params).json()
	for item in data['results']['bindings']:
		uri = item['e']['value']
	qnr = ''
	m = re.search("http://www.wikidata.org/entity/", uri)
	if m!= None:	#if the word does not occur in the line, m will be None.
		qnr = uri[:m.start()] + uri[m.end():]
		
	return qnr

#Function to find the Q-number of a property using wikidata API:
def searchIdProp(prop):
	prop = str(prop)
	url = 'https://www.wikidata.org/w/api.php'
	params = {'action':'wbsearchentities',
		'language':'en',
		'format':'json',
		'type':'property'}

	params['search'] = prop.rstrip()
	json = requests.get(url,params).json()
	answer=[]
	for result in json['search']:
		answer.append(result['id'])
	return answer

def searchIdEnt(ent):
	ent = str(ent)
	url = 'https://www.wikidata.org/w/api.php'
	params = {'action':'wbsearchentities',
		'language':'en',
		'format':'json'}

	params['search'] = ent.rstrip()
	json = requests.get(url,params).json()
	for result in json['search']:
		return result ['id']
		

#Function find prop, ent and probably value:
def findItems(result):
	[prop, ent, value] = [None, None, None]
#	nlp = spacy.load('en_default')
#	result = nlp(sentence)
	for w in result:
		print("{} {} {} {} {}".format(w.lemma_,w.dep_,w.head.lemma_,w.pos_, w.ent_iob_))
	#Yes or no questions:
	stype = 'else'
	if result[0].lemma_ == 'be' or result[0].lemma_ == 'do':
		print('This is a yes-no question')
		#Type: is barbecuing a cooking technique? -> alle values doorzoeken.
		for x in result:
			if x.dep_=='ROOT' and (x.lemma_=='contain' or x.lemma_ == 'have'):
				stype = 'contain'
			if x.dep_ == 'attr':
				stype = x.dep_
		for w in result:
			if w.dep_ == 'ROOT':
				if stype == 'attr':
					#attr sentence
					print('This is an attr sentence')
					for x in result:
						if x.head == w and x.dep_ == 'attr':
							prop = x.lemma_
							prop = getFullEntity(x)
							print('x is now: ', prop)
						if x.head == w and (x.dep_ == 'nsubj' or x.dep_ == 'acomp'):
							if x.pos == 'PROPN':
								value = x.text
							else:
								value = x.lemma_
							
						if x.dep_ == 'pobj':
							ent = x.text
							ent = getFullEntity(x)
							print('x is now: ', ent)
							#for y in x.subtree:
							#	print(y.lemma_)
							#	if (y.pos_ == 'NOUN' or y.pos_ == 'PROPN' or y.dep_ == 'compound'):
									#if y.pos_ == 'PROPN': # a proper name
							#		ent  = ' '.join(compoundName(y))
							#		print('ent: '+ ent)
								
				if stype == 'contain':
					print('this is a contain sentence')
					for x in result:
						if x.head== w and x.dep_=='nsubj':
							ent = x.lemma_
						if x.head== w and x.dep_== 'dobj':
							value = x.lemma_
						prop = 'contain'	
				if stype == 'else':
					#rest
					print('this is another sentence')
					for x in result:
						if x.head == w and x.dep_ == 'nsubj' :
							prop = x.lemma_
							if x.pos_ == 'PROPN': # a proper name
								prop  = ' '.join(compoundName(x))
							else:
								prop = x.lemma_ #make this more general	
							print('prop: ' +prop)
						if x.dep_ == 'pobj':
							ent = x.lemma_
							print('ent: '+ent)
							for y in x.subtree:
								print(y.lemma_ + y.pos_)
								if (y.pos_ == 'NOUN' or y.pos_ == 'PROPN'):
									if y.pos_ == 'PROPN': # a proper name
										ent  = ' '.join(compoundName(y))
	#									print('value: '+value
						if x.head == w and (x.dep_ == 'acomp' or x.dep_ == 'dobj'):
							value = x.lemma_		
				if ent == None: # Is an apple fruit?
					print('before: '+ prop,ent,value)
					ent = value
					value = prop
					prop = None
					#print(prop)
					
					
				print(prop, ent, value)
				return [prop, ent, value];
				print('I did not find the correct property and entity, sorry')
				return [0,0,0]
#	else:
#		if result[0].lemma_ =='DO':
#			....
			
			
		#where questions
	else:
		if result[0].lemma_ == 'where':
#			print('This is a where-question')
			prop = 'location'
			for w in result:
				if w.dep_== 'ROOT':
					for x in result:
						if x.head == w and (x.dep_ == 'nsubj' or x.dep_ == 'nsubjpass'):
							if x.pos_ == 'PROPN': # a proper name
									ent  = ' '.join(compoundName(x))
							else:
								ent = x.lemma_ #make this more general	
#							print(ent)
							return [prop, ent, None];
					print('I did not find the correct property and entity, sorry')
					return [0,0,0]
		#when-questions
	#else if result(0).lemma_ == 'when':
	#	...
		
	#what is the x of y questions new:
		else:
			if result[0].lemma_ == 'what' or result[0].lemma_ == 'who' or result[0].pos_ == 'VERB':
#				print('This is a what or who question')
				for w in result:
					#print("{} {} {}".format(w.lemma_,w.dep_,w.head.lemma_))
					if w.dep_ == 'ROOT': # w = be:
#						print('ROot: '+ w.lemma_)
						prop = None
						ent = None
						case = None
						for x in result:
							if (x.pos_ == 'NOUN' or (x.pos_ == 'PROPN'and lastOfComp(result, x) == 1)) and (x.lemma_ != 'what' and x.lemma_ != 'who'):
								if prop == None:
									if x.pos_ == 'PROPN': # a proper name
										prop  = ' '.join(compoundName(x))
									else:
										prop = findCompounds(result, x, 'amod')
									for z in result:
										if z.head == x and z.dep_ == 'case':
											case = 'prop'
#									print('prop: ' + prop)
								else:
									if x.pos_ == 'PROPN': # a proper name
										ent  = ' '.join(compoundName(x))
									else:
										ent = findCompounds(result, x, 'amod')
									for z in result:
										if z.head == x and z.dep_ == 'case':
											case = 'ent'	
#									print('ent: ' + ent)	
						if ent ==None or  prop==None:
							if ent !=None:
								print("this is a what is ... question")
								return [prop, ent, value]
							if prop != None:
								print("this is a what is ... question")								
								return [ent, prop, value]
							print('Either the property or the entity was not found, sorry.')
							return[0,0,0]
#						print(case)
						if case == 'prop':
							temp = prop
							prop = ent
							ent = temp
						if case != None:
							ent = ent.replace(' \'s', '')
						#[prop, ent] = caseCheck(prop, ent)
#						print('prop ' + prop + ', ent '+ ent)							
						return [prop, ent, None]
			else:
				print('I cannot (yet) deal with such types of questions.')
				return [0,0,0]

def getFullEntity(token):
	ret = token.text
	for child in token.children:
		if child.dep_ == 'amod' or child.dep_ == 'compound':
			ent = ' '.join(child.text)
			ret = child.text + ' ' +ret
	return ret		
			



#Function to check whether a proper noun is the last or only of compound:
def lastOfComp(result, x):
	for w in result:
		if x.head == w and x.dep_ == 'compound':
#			print('not last of compound')
			return 0
#	print('last of compound') 
	return 1
		
#Function to find dependencies in result:	
def findDep(result, word, dep):
	for x in result:
		if x.head == word and x.dep_ == dep:
			return x
	return None

#Function to find compounds:
def findCompounds(result, word, dep):
	compound = findDep(result, word, 'compound')
	if compound != None:
		answer = compound.lemma_ + ' ' + word.lemma_
	else:
		compound = findDep(result, word, dep)
		if compound != None:
			answer = compound.lemma_ + ' ' + word.lemma_
		else:
			answer = word.lemma_
	return answer

#Function to find full proper names:
def compoundName(name):
	subject=[]
	for d in name.subtree:
		subject.append(d.text)
	return subject


#Function to extract the x and y from a 'Who/What is the x of y' question: (not used for assignment4)
def extractWords(line):
	line = line.rstrip() # removes newline
	# remove articles:
	m = re.search(" the ", line)
	if m!= None:	#if the word does not occur in the line, m will be None.
		line = line[:m.start()] + ' ' + line[m.end():]
	m = re.search(" a ", line)
	if m!= None:
		line = line[:m.start()] + ' ' + line[m.end():]
	m = re.search(" an ", line)
	if m!= None:
		line = line[:m.start()] + ' ' + line[m.end():]
	# remove Who or What at the begin of the sentence to make both types possible:
	m = re.search("Who ", line)
	if m!= None:
		line = line[:m.start()] + line[m.end():]
	m = re.search("What ", line)
	if m!= None:
		line = line[:m.start()] + line[m.end():]
	
	#Find the property and entity to be used:	
	m = re.search('is (.*) of (.*)\?', line)
	if m == None:#wrong spelling
		print("Probably you made a spelling mistake")
		return [0,0]
	else:
		prop = m.group(1)
		ent = m.group(2)
		return [prop, ent]

def printExampleQueries():
	print("Some example questions:  \nWhat is the birthdate of Jamie Oliver?  " +
	" \nWhat is KFC's revenue?" + 
	"\nIs Germany the country of origin of Paella? \nWhat is a dandelion's latin name?" +
	" \nWhat is Jamie Oliver's nationality? " +
	"\nIs Amsterdam the capital of the Netherlands? \nWhere is the Great Barrier Reef located? \nIs red the colour of an apple?" +
	" \nWhat ingredients does hutspot consist of? \nWhere is Rotterdam?")
	return

if __name__ == "__main__":
	main(sys.argv)

##############################################
#The following function is only made for using wikidataAPI instead of wikipedia anchor texts.


