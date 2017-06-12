#!/usr/bin/python3

import sys
import spacy
import re
import socket

from sharedcode import *

from s2020947 import get_answer_s2020947
from s2576597 import get_answer_s2576597
from s2995263 import get_answer_s2995263




# Answer selection
def selectAnswers(line, answers1, answers2, answers3):
    output = list(set(answers1 + answers2 + answers3))
    # "Yes Yes No" => "Yes No" => "Yes"
    if "Yes" in output or "yes" in output and not " or " in line:
        return ["Yes"]
    # Check if there are two identical answers
    allanswers = [answers1, answers2, answers3]
    # Remove duplicates
    if "founded"  in line and answers2 != []:
	    return answers2
    for List in allanswers:
        occurences = 0
        for List2 in allanswers:
            if List == List2 and List:
                occurences += 1
        if occurences > 1:
            return List
    if answers1:
        return answers1
    if answers2:
        return answers2
    return answers3



# Start

if socket.gethostname() == 'Aspire' or socket.gethostname() == 'DESKTOP-6OMO0PT':
    nlp = spacy.load("en")
else:
    nlp = spacy.load("en_default")
    
print("\nReading anchor_texts to dictionary(about 20 seconds)\nPlease wait...")
start = time.time()
anchor_dict = init_anchor_dict()
print("Completed in " + str(time.time()-start) + " seconds.\n")

debugLog("Ready")

for line in sys.stdin:
    temp = re.split('\t', line)
    if len(temp) == 2:
        questionid = temp[0]
        question = temp[1]
    else:
        questionid = "0"
        question = line
    answers1 = answers2 = answers3 = []
    #try:
    answers2 = get_answer_s2020947(question, nlp, anchor_dict)
    #except:
    #    pass
    #try:
    answers1 = get_answer_s2576597(question, nlp, anchor_dict)
    #except:
    #    pass
    try:
        answers3 = get_answer_s2995263(question, nlp)
    except:
        pass
    #print(answers1, answers2, answers3)
    selected = selectAnswers(line, answers1, answers2, answers3)
    output = []
    output.append(str(questionid))
    for item in selected:
        output.append(str(item))
    print(str.join("\t", output))
