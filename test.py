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

if socket.gethostname() == 'Aspire' or socket.gethostname() == 'DESKTOP-6OMO0PT':
    nlp = spacy.load("en")
else:
    nlp = spacy.load("en_default")

debugLog("Ready")

xmldoc = minidom.parse("data/cleanquestions.xml")
items = xmldoc.getElementsByTagName('question')

correct = 0
total = 0


def printStats():
    print("####")
    print("Total:", total)
    print("Correct:", correct, "(", float(correct) / float(total), "%)")
    print("####\n")


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
    p1 = p2 = p3 = p4 = []
    try:
      p1 = get_answer_s2020947(question, nlp)
    except:
      print("Exception in s2020947")
    try:
      p2 = get_answer_s2576597(question, nlp)
    except:
      print("Exception in s2576597")
    try:
      p3 = get_answer_s2995263(question, nlp)
    except:
      print("Exception in s2995263")
    try:
      p4 = get_answer_s3248216(question, nlp)
    except:
      print("Exception in s3248216")
    answers = list(set(p1 + p2 + p3 + p4))
    if answers == expectedoutput:
        correct = correct + 1
    else:
        print("### Wrong answer ###")
        print("Question:", question)
        print("Expected:", expectedoutput)
        print("Result:", answers)
    total = total + 1
    printStats()
