from learnparse import getKey, makeTree, treeToArray, getArrayOfNounsAndVerbs

def isBooleanQuestion(key, array, line):
  booleanKeys = ['ROOTauxpassnpadvmodoprd', 'ROOTauxnsubjpreppobjacomppreppobj', 'ROOTnsubjattr', 'ROOTauxnsubjdobj', 'ROOTattrappos', 'ROOTauxnsubjpreppobj', 'ROOTattracompneg', 'ROOTnsubjappospreppobj', 'ROOTauxnsubjdobjpreppobj', 'ROOTauxnsubjpassauxpasspreppobj', 'ROOTnsubjdobj', 'ROOTauxpassauxoprd', 'ROOTnsubjattrpreppobj', 'ROOTnsubjnsubjattr', 'ROOTauxdobjxcompauxpasspreppobj', 'ROOTattr', 'ROOTauxnsubjnmoddobjpreppobj', 'ROOTauxdobjpreppobj', 'ROOTnsubjacomp']
  #Check if the question has proper yes-no key
  if key not in booleanKeys:
    return False
  #Check if first word is a verb
  firstWord = line.split(' ')[0]
  if firstWord.lower() == 'how':
    return False
  for token in array:
    if token.text == firstWord:
      if not token.pos_ == 'VERB':
        return False
      break
  return True

def isWhatIsQuestion(key, line, nlp):
  keys = ['ROOTadvmodauxadvmoddobj','ROOTnsubjaux','ROOTpobjnsubj','ROOTdobj','ROOTattrnsubj','ROOTnsubjpassauxauxpassoprd','ROOTnsubjnsubj']#'ROOTnsubjattr'
  if key in keys:
    return True
  splitted = line.split(' ')
  first = splitted[0].lower()
  second = splitted[1].lower()
  if (first == 'what' or first == 'who') and (second == 'is' or second == 'are') and len(getArrayOfNounsAndVerbs(line, nlp)) == 1:
    return True
  return False
  
def questionType(line, nlp):
  key = getKey(line, nlp)
  array = treeToArray(makeTree(line, nlp))
  #Boolean
  if isBooleanQuestion(key, array, line):
    return "boolean"
  #Count
  #What is
  if isWhatIsQuestion(key, line, nlp):
    return "whatis"
  #X and Y
  return "XandY"
