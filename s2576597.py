#!/usr/bin/python3
import sys
sys.path.append('./s2576597')
from xylib import create_and_fire_query
from switch import questionType
from boolean import solveBooleanQuestion
from whatislib import solveWhatIsQuestion

def get_answer_s2576597(line, nlp):
  ret = []

  #Switch over question types
  qType = questionType(line, nlp)
  if qType == "boolean":
    ret =  solveBooleanQuestion(line, nlp)
  elif qType == "whatis":
    ret = solveWhatIsQuestion(line, nlp)

  if ret:
    return ret
  else:#if there are no answers just try x and y
    return create_and_fire_query(line, nlp)
