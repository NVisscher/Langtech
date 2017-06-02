#!/usr/bin

import sys
import spacy
import re
import socket

from sharedcode import *

from xml.dom import minidom

from s2020947 import get_answer_s2020947
from s2576597 import get_answer_s2576597
from s2995263 import get_answer_s2995263
from s3248216 import get_answer_s3248216

if socket.gethostname() == 'Aspire':
	nlp = spacy.load("en")
else:
	nlp = spacy.load("en_default")

debugLog("Ready")


xmldoc = minidom.parse("data/allquestions.xml")
items = xmldoc.getElementsByTagName('question')

correct = 0
total = len(items)

for item in items:
	# Question text
	question = item.getElementsByTagName('string')[0].firstChild.nodeValue
	# Answers
	answers = item.getElementsByTagName('answer')
	expectedoutput = []
	for answer in answers:
		expectedoutput.append(answer.getElementsByTagName('string')[0].firstChild.nodeValue)
	expectedoutput = list(set(expectedoutput))
	# Run the question.
	p1 = get_answer_s2020947(question, nlp)
	p2 = get_answer_s2576597(question, nlp)
	p3 = get_answer_s2995263(question, nlp)
	p4 = get_answer_s3248216(question, nlp)
	answers = list(set(p1 + p2 + p3 + p4))
	if answers == expectedoutput:
		correct = correct + 1
	else:
		print("### Wrong answer ###")
		print("Question:", question)
		print("Expected:", expectedoutput)
		print("Result:", answers)

print("####")
print("Total:", total)
print("Correct:", correct, "(", float(correct)/float(total), "%")

