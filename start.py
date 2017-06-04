#!/usr/bin/python3

import sys
import spacy
import re
import socket

from sharedcode import *

from s2020947 import get_answer_s2020947
from s2576597 import get_answer_s2576597
from s2995263 import get_answer_s2995263
from s3248216 import get_answer_s3248216


# Answer selection

def selectAnswers(answers):
    # Remove duplicates
    output = list(set(answers))
    # "Yes Yes No" => "Yes No" => "Yes"
    if "Yes" in answers:
        output = ["Yes"]
    return output


# Start

if socket.gethostname() == 'Aspire' or socket.gethostname() == 'DESKTOP-6OMO0PT':
    nlp = spacy.load("en")
else:
    nlp = spacy.load("en_default")

debugLog("Ready")

for line in sys.stdin:
    answers = []
    temp = re.split('\t', line)
    if len(temp) == 2:
        questionid = temp[0]
        question = temp[1]
    else:
        questionid = "0"
        question = line
    answers = answers + get_answer_s2020947(question, nlp)
    answers = answers + get_answer_s2576597(question, nlp)
    answers = answers + get_answer_s2995263(question, nlp)
    answers = answers + get_answer_s3248216(question, nlp)
    selected = selectAnswers(answers)
    output = []
    output.append(str(questionid))
    for item in selected:
        output.append(str(item))
    print(str.join("\t", output))
