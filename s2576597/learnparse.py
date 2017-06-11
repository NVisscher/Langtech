import sys
import spacy
import copy


class MyToken:
  def __init__(self, text, pos, tag, dep, head, lemma):
    self.text = text
    self.dep_ = dep
    self.pos_ = pos
    self.tag_ = tag
    self.head = head
    self.conj = False
    self.extended = False
    self.lemma = lemma

def isUsefulPos(w):
  pos = w.pos_.lower()
  if pos == 'sym' or pos == 'punct' or pos == 'det':# or pos == 'adj': #Adjetives go away with nouns automatically
    return False
  if pos == 'adv' and not isUsefulPos(w.head):
    return False
  return True

def isAddable(w):
  return (w.dep_ == 'amod' or w.dep_ == 'compound' or w.dep_ == 'poss') #also use adjetives # and w.pos_.lower() == 'adj') << achter amod	

def getAddable(token):
  add = ''
  for child in token.children:
    if isAddable(child):
      add += getAddable(child)
  return add + token.text + " "

def isAfterAddable(w):
  return (w.dep_ == 'cc' or w.dep_ == 'conj')

def getAfterAddable(token):
  add = ''
  for child in token.children:
    if isAddable(child):
      add += getAddable(child)
  return " " + add + token.text

def tree(token):
  if token.n_lefts+token.n_rights > 0:
    ret = []
    add = ''
    afteradd = ''
    for child in token.children:
      if isAddable(child):
        add += getAddable(child)
        continue
      if isAfterAddable(child):
        afteradd += getAfterAddable(child)
        continue
      if isUsefulPos(child):
        ret.append(child);
    #ret.sort(key = lambda x: x.dep_)# Will get less keys but also less informative(because of order)
    rettoken = MyToken(add + token.text + afteradd, token.pos_, token.tag_, token.dep_, token.head, token.lemma_)
    if not afteradd == '':
      rettoken.conj = True
      rettoken.extended = True
    if not add == '':
      rettoken.extended = True
    return [rettoken, [tree(child) for child in ret]]
  else:
    return [MyToken(token.text, token.pos_, token.tag_, token.dep_, token.head, token.lemma_)]

def treeToString(tree):
  ret = tree[0].dep_.split("||")[0]
  if len(tree) > 1:
    for child in tree[1]:
      ret += treeToString(child)
  return ret

def treeToArray(tree):
  ret = []
  ret.append(tree[0])
  if len(tree) > 1:
    for child in tree[1]:
      ret.extend(treeToArray(child))
  return ret

def makeTree(line, nlp):
  result = nlp(line)
  for line in result.sents:
    return tree(line.root)

def getKey(line, nlp):
  return treeToString(makeTree(line, nlp))

def changeText(w):
  #could maybe use lemma here
  text = w.text
  if not w.extended and not '-' in text:
    text = text.lower()
  if w.pos_ == 'NOUN' and not w.extended:
    text = w.lemma
  if text[:5] == 'main ':
    text = text[5:]
  if text[:5] == 'many ':
    text = text[5:]
  if text[-8:] == ' consist':
    text = text[:-8]
  if text == 'where':
    text = 'origin'
  if text == 'when':
    text = 'date'
  if text == 'kind' or text == 'type':
    text = 'subclass'
  w.text = text
  return w
  
def getArrayOfNounsAndVerbs(line, nlp):
  result = treeToArray(makeTree(line, nlp))
  #result = translateSentece(line)
  ret = []
  for w in result:
    if w.pos_ == 'NOUN' or w.pos_ == 'PROPN' or w.pos_ == 'VERB' or (w.pos_ == 'ADV' and w.head.pos_ == 'VERB'):
      w = changeText(w)
      ret.append(w.text)
  return ret

def getArrayOfNouns(line, nlp):
  result = treeToArray(makeTree(line, nlp))
  #result = translateSentece(line)
  ret = []
  for w in result:
    if w.pos_ == 'NOUN' or w.pos_ == 'PROPN' or (w.pos_ == 'ADV' and w.head.pos_ == 'VERB'):
      w = changeText(w)
      ret.append(w.text)
  return ret

def skip(word):
  badwords = ['will', 'are', 'do', 'does', 'what', 'is', 'who', 'whom', 'why', 'can', "'s", 'was', 'did', 'get', 'give', 'have', 'has', 'there', 'how', 'also', 'be', 'list']
  if word.lower() in badwords:
    return True
  return False

def get_nouns_from_best_options(proporents, bestoptions):
  ret = []
  idx = bestoptions.index(max(bestoptions))
  while not (bestoptions[idx] == 0):
    if idx > len(proporents)-1:
      break
    bestoptions[idx] = 0
    if not skip(proporents[idx]):
      ret.append(proporents[idx])
    idx = bestoptions.index(max(bestoptions))
  return ret

def remove_bad_entities(ents):
  bad_ents = ['origin','come','subclass',"country", "city", "produced", "used", "make"]
  for ent in ents:
    if ent in bad_ents:
      ents.remove(ent)

def parse_question(line, nlp):
  key = getKey(line, nlp)
  proporents = getArrayOfNounsAndVerbs(line, nlp)
  if key in basicd:
    bestoptions = copy.deepcopy(basicd[key])
  else:
    return [[],[]]
  #Get list of best entities
  ents = get_nouns_from_best_options(proporents, bestoptions[0])
  remove_bad_entities(ents)
  #Get list of best properties
  props = get_nouns_from_best_options(proporents, bestoptions[1])
  return [ents, props]

basicd = {
  'ROOTdobjdetauxnsubjprep': [[0, 1, 0, 1, 3], [2, 3, 0, 0, 0]],
  'ROOTdobjauxdobj': [[0, 0, 0], [0, 0, 0]],
  'ROOTdetauxprep': [[0, 0, 0], [0, 0, 0]],
  'ROOTnsubjdetattradvmodprep': [[0, 0, 1, 0], [0, 1, 0, 0]],
  'ROOTadvmodauxpassnpadvmod': [[0, 0, 0, 5], [2, 3, 0, 0]],
  'ROOTdobjnsubjauxadvmod': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTadvcladvmodnsubjpass': [[0, 0, 0, 4], [2, 0, 2, 0]],
  'ROOTprepnsubjpassdetpreppobjauxpassnpadvmod': [[0, 0, 0, 0, 1], [1, 0, 0, 0, 0]],
  'ROOTnsubjpassauxpassadvmodpreppobjdet': [[0, 2, 0, 0, 0], [0, 0, 0, 0, 2]],
  'ROOTdobjdetdobjprep': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjattrrelclnsubjdobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTacompadvmodnsubj': [[0, 0, 1], [0, 1, 0]],
  'ROOTadvmodauxpassadvmodprep': [[1, 0, 0, 0], [0, 1, 0, 0]],
  'ROOTauxpassmarknsubjdetnpadvmod': [[0, 0, 0, 1], [1, 0, 0, 0]],
  'ROOTnsubjpassdetauxpassadvmodpreppobjaclauxdobj': [[0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0]],
  'ROOTdobjdobjprep': [[0, 0, 0], [0, 0, 0]],
  'ROOTauxnsubjpassauxpasspreppobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTpobjdetauxnsubjprep': [[0, 0, 0, 0, 9], [5, 4, 0, 0, 0]],
  'ROOTmarkauxpassattrneg': [[0, 0, 0, 1], [1, 0, 0, 0]],
  'ROOTadvmodnsubjaclprep': [[0, 0, 3, 0], [0, 0, 0, 3]],
  'ROOTnsubjattrcaseaclagent': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjauxnsubjpreppobj': [[0, 0, 0, 1], [1, 0, 0, 0]],
  'ROOTpreppobjdetauxnsubj': [[0, 0, 0, 0, 2], [1, 1, 0, 0, 0]],
  'ROOTadvmodauxpassnsubj': [[0, 0, 0, 7], [3, 4, 0, 0]],
  'ROOTdobjdetaux': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTpcompnsubjattracl': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTpobjnsubjpreppobj': [[0, 0, 0, 5], [0, 0, 5, 0]],
  'ROOTnsubjpasspreppobjauxpassadvmodpreppobj': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTpobjnpadvmoddetnsubj': [[0, 0, 0], [0, 0, 0]],
  'ROOTnsubjpassauxpassxcompprep': [[1, 0, 0, 0], [0, 0, 0, 1]],
  'ROOTnsubjnsubjpreppobjpreppobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTnsubjattraclprep': [[0, 0, 9, 0], [0, 0, 0, 9]],
  'ROOTnsubjpassauxpassattrprep': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjacomppreppobj': [[0, 0, 0], [0, 0, 0]],
  'ROOTpreppcompdobjauxnsubj': [[0, 0, 0, 1], [1, 0, 0, 0]],
  'ROOTpreppcompdetauxnsubjprep': [[0, 0, 0, 2], [1, 1, 0, 0]],
  'ROOTnsubjattr': [[0, 0, 0], [0, 0, 0]],
  'ROOTpobjdetpreppobjauxnsubjprep': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOToprdauxpassnsubjpreppobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTdobjauxaclprep': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTattrdetpreppobjacomp': [[0, 0, 0, 1], [0, 1, 0, 0]],
  'ROOTnsubjdobjcase': [[0, 0, 0], [0, 0, 0]],
  'ROOTdobjdobjauxnsubj': [[0, 0, 0, 0, 2], [0, 0, 2, 0, 0]],
  'ROOTattrattrpreppobj': [[0, 0, 0, 25], [0, 0, 25, 0]],
  'ROOTauxpassauxnsubjprep': [[0, 0, 0, 1], [1, 0, 0, 0]],
  'ROOToprdauxnsubjoprdpreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTattrnsubjpreppobjcasepreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTdobjnsubjpassauxpassxcompauxdobj': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTprepnsubjpassdetauxnsubjpassauxpass': [[0, 0, 0, 0, 1, 0], [0, 1, 0, 0, 0, 0]],
  'ROOTpobjnsubjpassauxpasspreppcompdobj': [[0, 0, 0, 0, 0, 1], [0, 0, 1, 0, 0, 0]],
  'ROOTpreppcompdetnsubjpreppobj': [[0, 0, 0, 1], [0, 1, 0, 0]],
  'ROOTattrnsubjadvmod': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTadvmodauxnsubjccompnsubjattr': [[0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 0, 1]],
  'ROOTadvmodnsubjprep': [[0, 0, 3], [0, 3, 0]],
  'ROOTpcompnsubjnsubjapposprep': [[0, 0, 1, 0], [0, 0, 0, 1]],
  'ROOTpreppobjnsubjpassauxpassnpadvmod': [[0, 0, 0, 1], [1, 0, 0, 0]],
  'ROOTdativedobjpreppobjrelclnsubjdobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTattrnsubjprep': [[0, 0, 0], [0, 0, 0]],
  'ROOTattrappos': [[0, 0, 0], [0, 0, 0]],
  'ROOTdativedobjrelclnsubjpreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTmarkauxpassnsubjnsubjpreppobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTadvmodauxnsubj': [[0, 0, 0, 5], [2, 3, 0, 0]],
  'ROOTnsubjpassdetauxpasspreppobj': [[0, 0, 0, 3], [0, 3, 0, 0]],
  'ROOTdobjaux': [[0, 0, 0], [0, 0, 0]],
  'ROOTadvmodattrapposacl': [[0, 0, 0, 2, 0], [0, 1, 0, 0, 1]],
  'ROOTadvmodauxadvmodprep': [[4, 0, 0, 0], [0, 2, 0, 2]],
  'ROOTnpadvmoddetattrccompnsubj': [[0, 0, 0, 0, 0, 2], [0, 1, 0, 0, 1, 0]],
  'ROOTpobjauxpassnsubjpassprep': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjpassauxpasspreppobjpreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTmarknsubjpassdetauxpassdobj': [[1, 0, 0, 0], [0, 0, 0, 1]],
  'ROOTattrdetattr': [[0, 0, 0, 1], [0, 1, 0, 0]],
  'ROOTadvmodnsubjauxprep': [[0, 0, 4, 0], [2, 2, 0, 0]],
  'ROOTpreppcompdetnsubjapposacl': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTprepnsubjdetauxdobj': [[2, 0, 0, 0], [0, 1, 0, 1]],
  'ROOTnsubjccompauxnsubjadvmod': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTattrnsubjpreppobjpreppobjappos': [[0, 0, 0, 0, 0, 2], [0, 0, 1, 1, 0, 0]],
  'ROOTattrattrpreppobjcase': [[0, 0, 0, 1], [0, 0, 1, 0]],
  'ROOTprepnsubjpassdetpreppobjauxpassoprd': [[1, 0, 0, 0], [0, 0, 1, 0]],
  'ROOTpreppobjdetnsubjacl': [[0, 0, 2, 0], [0, 1, 0, 1]],
  'ROOTnsubjadvmodpreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjacomp': [[0, 0], [0, 0]],
  'ROOTattrnsubjpreppobjaclpreppobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTdobjpreppobjappos': [[0, 0, 0, 1], [0, 0, 1, 0]],
  'ROOTdobjnummodrelclnsubjdobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjdetpreppobjccompadvmod': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTattrnsubjnummodpreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTpreppcompdetaux': [[1, 0, 0], [0, 1, 0]],
  'ROOTnsubjdetpreppobjadvmod': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjpassdetauxpassadvclauxdobj': [[0, 0, 0, 0, 1], [0, 1, 0, 0, 0]],
  'ROOTnsubjdetattraclprep': [[0, 0, 1, 2, 0], [0, 0, 0, 1, 2]],
  'ROOTdobjdetauxdobjprep': [[3, 0, 0, 0, 0], [0, 2, 0, 0, 1]],
  'ROOTnsubjauxprepadvmodprep': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTdobjrelclnsubjdobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjdetdobjadvmod': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjattrpreppcompdet': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTadvmodauxccompnsubj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTattrdetnsubj': [[0, 0, 0, 1], [0, 1, 0, 0]],
  'ROOTnsubjauxnsubj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjxcompauxdobjccompdobjauxnsubj': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTpobjauxpassnpadvmodprep': [[0, 0, 0, 3], [3, 0, 0, 0]],
  'ROOTauxpassadvmodnsubjpass': [[0, 0, 0, 4], [2, 0, 2, 0]],
  'ROOTadvmodnsubjpreppobj': [[0, 0, 0, 10], [0, 5, 5, 0]],
  'ROOTdobjauxnsubjadvmod': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTadvmodauxpassnsubjpass': [[0, 0, 0, 13], [5, 8, 0, 0]],
  'ROOTpcomppobjnsubjnsubj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjpassauxpassadvmodprep': [[0, 0, 0], [0, 0, 0]],
  'ROOTnsubjauxprep': [[0, 0, 0], [0, 0, 0]],
  'ROOTpobjauxnsubjpreppcomp': [[0, 0, 0, 2], [1, 1, 0, 0]],
  'ROOTauxpasspreppobjadvmod': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTadvmodauxnsubjdobj': [[0, 0, 0, 2], [0, 2, 0, 0]],
  'ROOTprepdobjdetpreppobjauxnsubjdobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTadvmodnsubjaclpreppobj': [[0, 0, 0, 0, 1], [0, 0, 1, 0, 0]],
  'ROOTnsubjnmod': [[0, 0, 0], [0, 0, 0]],
  'ROOTdobjdetpreppobjauxnsubjprep': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTnsubjdetdobj': [[0, 0, 2], [1, 1, 0]],
  'ROOTnsubjxcompauxpreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTpreppcompdetadvmodccompnsubj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTnsubjdetadvmoddobj': [[0, 0, 1], [0, 1, 0]],
  'ROOTnsubjdetpreppobjacomp': [[0, 0, 0], [0, 0, 0]],
  'ROOTnsubjdobjdetauxprep': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTprepnsubjdetacompadvmodccompmarknsubjauxdobj': [[0, 0, 0, 0, 1], [0, 1, 0, 0, 0]],
  'ROOTadvcladvmodauxpass': [[0, 1, 0, 0], [0, 0, 1, 0]],
  'ROOTnsubjdetattrpreppobjpreppobjacloprd': [[0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0]],
  'ROOTpobjdetnsubjauxprep': [[0, 0, 0, 6, 0], [3, 3, 0, 0, 0]],
  'ROOTpcompattrnsubjattr': [[0, 0, 0, 1], [0, 0, 1, 0]],
  'ROOTpcompattrnsubjacl': [[0, 0, 1, 0], [0, 0, 0, 1]],
  'ROOTnsubjnsubjattrprep': [[0, 0, 0], [0, 0, 0]],
  'ROOTadvmodauxdobjprep': [[6, 0, 0, 0], [0, 3, 0, 3]],
  'ROOTdativedobjnummodpreppobj': [[0, 0, 0], [0, 0, 0]],
  'ROOTnsubjdetattrpreppobj': [[0, 0, 0, 2, 3], [0, 2, 1, 2, 0]],
  'ROOTauxpasspreppobjdativeapposcase': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTadvmodauxadvmoddobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTprepnsubjdetadvmod': [[0, 0, 0, 2], [1, 1, 0, 0]],
  'ROOTmarknsubjdetattracl': [[0, 0, 1, 0], [0, 0, 0, 1]],
  'ROOTauxpassattrnsubjpassagent': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTadvmodnsubjpreppobjcaseacl': [[0, 0, 0, 2, 0], [0, 0, 2, 0, 0]],
  'ROOTnsubjattrpreppobjpreppobjdet': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTnsubjpassdetauxauxpasspreppobj': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTprepnsubjpassdetauxpassattradvmod': [[0, 0, 0, 1], [0, 1, 0, 0]],
  'ROOTdobjnsubjadvmodprep': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjdobjxcompadvmodauxdobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTadvmodnsubjnsubjprep': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTattrnsubjpreppobjacl': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTpobjauxnsubjcaseprep': [[0, 0, 0, 2], [1, 1, 0, 0]],
  'ROOTnsubjattradvmodprep': [[0, 0, 0], [0, 0, 0]],
  'ROOTnsubjpreppobj': [[0, 0, 2], [1, 1, 0]],
  'ROOTauxpassadvmodnegappos': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTnsubjacompaclpreppobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTauxpassattrnsubjpreppobjdobj': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTnsubjpassdetauxpassagentpobj': [[0, 0, 0, 2, 2], [3, 1, 0, 0, 0]],
  'ROOTpobjnsubjpreppobjrelclauxpreppobj': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTauxpasspreppcompdetnsubjappos': [[0, 0, 0, 0, 0, 2], [1, 0, 1, 0, 0, 0]],
  'ROOTnsubjdetauxnsubjnummodapposprep': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTauxpassadvmodnsubjpassappos': [[0, 0, 0, 0, 2], [1, 0, 1, 0, 0]],
  'ROOTadvmodauxpassnsubjpassadvmod': [[0, 0, 0, 2, 0], [1, 1, 0, 0, 0]],
  'ROOTadvmodnsubjdetdobj': [[0, 0, 1], [0, 1, 0]],
  'ROOTdobjdetauxnsubjxcompauxdobj': [[0, 0, 0, 0, 2], [0, 2, 0, 0, 0]],
  'ROOTnsubjpassdetauxpasspreppobjadvmod': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTadvmodauxnsubjxcompdobj': [[0, 0, 0, 0, 1], [0, 1, 0, 0, 0]],
  'ROOTpreppcompdetauxnsubj': [[0, 0, 0, 4, 2], [3, 3, 0, 0, 0]],
  'ROOTpobjnsubj': [[0, 0, 0], [0, 0, 0]],
  'ROOTnsubjdobjdobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTdobjdetauxnsubjadvmod': [[0, 0, 0, 1, 0], [0, 1, 0, 0, 0]],
  'ROOTauxpassadvmodneg': [[0, 0, 0, 1], [0, 0, 1, 0]],
  'ROOTpreppcompdetccompnsubj': [[0, 0, 0, 2, 3], [0, 3, 1, 1, 0]],
  'ROOTnsubjpassauxpasspreppcompnsubjadvmoddobj': [[0, 1, 0, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0, 0]],
  'ROOTpcompadvmodauxpassmeta': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTdobjnsubj': [[0, 0, 0], [0, 0, 0]],
  'ROOTadvmodauxnsubjpassauxpassprep': [[0, 0, 0, 1, 0], [1, 0, 0, 0, 0]],
  'ROOTnsubjpassdetpreppobjauxpass': [[1, 0, 0, 0], [0, 1, 0, 0]],
  'ROOTnsubjdetpreppobjdobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTadvmodnsubjacl': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTauxprepnsubjdetnsubj': [[0, 0, 1, 0], [1, 0, 0, 0]],
  'ROOTattrdetpreppobjnsubj': [[0, 0, 0, 9], [0, 8, 1, 0]],
  'ROOTadvmodnsubjadvmodprep': [[0, 0, 1, 0], [0, 1, 0, 0]],
  'ROOTpobjnsubjauxprep': [[0, 0, 14, 0], [7, 7, 0, 0]],
  'ROOTdobjdetpreppobjauxnsubj': [[0, 0, 0, 0, 3, 0], [0, 1, 2, 0, 0, 0]],
  'ROOTattrnsubjaclpreppobj': [[0, 0, 0, 0, 8], [0, 0, 8, 0, 0]],
  'ROOTadvmodattracl': [[0, 0, 3, 0], [0, 1, 0, 2]],
  'ROOTnsubjdetccompnsubjnsubj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTdobjpreppobj': [[0, 0, 8], [0, 8, 0]],
  'ROOTadvmodauxccompnsubjprep': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTdobjauxnsubj': [[0, 0, 0, 3], [3, 0, 0, 0]],
  'ROOTdobjauxnsubjxcompauxdobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTattrnsubjpreppobj': [[0, 0, 0, 92], [0, 0, 92, 0]],
  'ROOTadvmodccompnpadvmod': [[0, 0, 0, 2], [0, 2, 0, 0]],
  'ROOTnsubjpassdetauxpasspreppcompdobj': [[0, 0, 0, 0, 1], [0, 1, 0, 0, 0]],
  'ROOTnsubjpassdetpreppobjauxpasspreppobj': [[0, 0, 0, 0, 1], [0, 1, 0, 0, 0]],
  'ROOTauxpassprepnsubjdetnsubjpasscase': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjpassauxpassacompprep': [[0, 0, 0], [0, 0, 0]],
  'ROOTpobjattraclpreppobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTnsubjpassauxpassprep': [[0, 0, 0], [0, 0, 0]],
  'ROOTauxnsubjnsubj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjdetdobjpreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjpassauxpasspreppobjdet': [[0, 2, 0, 0, 0], [1, 0, 0, 1, 0]],
  'ROOTpreppcompdetpreppobjnsubjaux': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTattrnsubjpreppobjpreppobj': [[0, 0, 0, 2, 64], [0, 0, 33, 33, 0]],
  'ROOTnsubjattraclpreppobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTadvmodnsubjpreppobjacl': [[0, 0, 0, 1, 0], [0, 0, 1, 0, 0]],
  'ROOTpobjauxnsubjnmodprep': [[0, 0, 0, 2, 0], [1, 1, 0, 0, 0]],
  'ROOTauxnsubjpreppobj': [[0, 0, 1, 0], [1, 0, 0, 0]],
  'ROOTpobjauxnsubjdobjprep': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTpreppobjnsubjacl': [[0, 0, 1, 0], [0, 0, 0, 1]],
  'ROOTattracompneg': [[0, 0, 0], [0, 0, 0]],
  'ROOTprepnpadvmoddetdobjdobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTpobjnsubjdobjaclpreppobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTnsubjpassdetauxpasspreppobjpreppobj': [[0, 0, 0, 0, 3], [1, 1, 0, 1, 0]],
  'ROOTnsubjpassauxauxpassoprd': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTdobjauxnsubjcase': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTmarknsubjdetdobj': [[0, 0, 0, 1], [0, 1, 0, 0]],
  'ROOTattrattraclprep': [[0, 0, 9, 0], [0, 0, 0, 9]],
  'ROOTauxpasspreppcompdetnsubjpass': [[0, 0, 0, 1], [0, 0, 1, 0]],
  'ROOTnsubjdobj': [[0, 0, 13], [13, 0, 0]],
  'ROOTadvmodattraclpreppobj': [[0, 0, 2, 0, 0], [0, 1, 0, 1, 0]],
  'ROOTdobjnsubjaux': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTauxpassnsubjpreppobjadvmodprep': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTpobjauxnsubjadvmodprep': [[0, 0, 0, 4, 0], [2, 2, 0, 0, 0]],
  'ROOTattrnsubj': [[0, 0, 0], [0, 0, 0]],
  'ROOTnsubjapposprep': [[0, 0, 1], [1, 0, 0]],
  'ROOTnsubjpassauxpassadvclauxdobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTprepattrdetnsubjappos': [[0, 0, 0, 2, 0], [0, 1, 0, 0, 1]],
  'ROOTnsubjpassauxpassxcompauxattrpreppobj': [[0, 0, 0, 0, 2], [2, 0, 0, 0, 0]],
  'ROOTnsubjnsubjattr': [[0, 0, 0], [0, 0, 0]],
  'ROOTnsubjpasspreppobjauxauxpasspreppobjpreppobj': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTnsubjpassauxpassxcompauxdobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTnsubjnsubj': [[0, 0, 0], [0, 0, 0]],
  'ROOTnsubjpasspreppobjauxpass': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTdobjdetpreppobjaux': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTpobjauxnsubjapposprep': [[0, 0, 0, 0, 2], [1, 1, 0, 0, 0]],
  'ROOTdobjauxnsubjnsubj': [[0, 0, 0, 0, 2], [0, 0, 0, 2, 0]],
  'ROOTpreppcompdet': [[0, 0], [0, 0]],
  'ROOTnsubjpreppobjdet': [[0, 2, 1], [2, 0, 1]],
  'ROOTdobjnsubjpassauxpasspreppobj': [[0, 0, 0, 0, 3], [0, 0, 3, 0, 0]],
  'ROOTprepnsubjdetpreppobjnsubjadvcl': [[0, 0, 0, 1, 0], [0, 1, 0, 0, 0]],
  'ROOTnsubjpassdetpreppobjauxpassnsubjprep': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTauxdobjnsubjnegcase': [[0, 0, 0, 1], [0, 0, 1, 0]],
  'ROOTattrnsubjpreppobjappos': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTattrnsubjrelclnsubjdobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTpreppobjdepauxnsubjprep': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjattrprep': [[0, 0, 0], [0, 0, 0]],
  'ROOTadvmodauxnsubjnsubj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTnsubjccompnsubjattrprep': [[0, 1, 0, 0], [0, 0, 0, 1]],
  'ROOTnsubjappospreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTauxnsubjdobjpreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTattrattrpreppobjappos': [[0, 0, 0, 0, 1], [0, 0, 1, 0, 0]],
  'ROOTauxpassnsubjattradvmodprep': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTattrcsubjnsubjpasspreppobjpreppobjnmodauxpassprep': [[0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]],
  'ROOTprepnsubjdetnsubj': [[0, 1, 2], [2, 1, 0]],
  'ROOTprepdobjdetauxnsubj': [[0, 3, 0, 4, 8], [8, 7, 0, 0, 0]],
  'ROOTdobjauxnsubjprep': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjdetpreppobjattr': [[0, 0, 0, 11], [0, 11, 0, 0]],
  'ROOTpcompnsubjdetpreppobjxcompdobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTnsubjpassdetauxpassadvmodpreppobj': [[0, 0, 0, 0, 5], [0, 3, 0, 2, 0]],
  'ROOTnsubjpassdetpreppobjauxpassxcompauxdobj': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTdobjauxpassnsubjprepprep': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTdobjdetauxnsubjpreppobj': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTnsubjattrpreppobj': [[0, 1, 0, 6], [0, 0, 7, 0]],
  'ROOTpreppobjdetpreppobjnsubjappos': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTnsubjpassdetauxpassxcompauxdobj': [[0, 0, 0, 0, 1, 2], [0, 3, 0, 0, 0, 0]],
  'ROOTnsubjpassauxpassnsubjpassprep': [[0, 0, 0, 2], [2, 0, 0, 0]],
  'ROOTprepattrdetnsubj': [[0, 0, 0, 2], [0, 2, 0, 0]],
  'ROOTadvcladvmodnsubjdobjnummod': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTpreppobjnsubjnsubjdobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTpreppcompdetattradvcladvmod': [[0, 0, 0, 1, 0, 0], [0, 1, 0, 0, 0, 0]],
  'ROOTdativedobjpreppobjappos': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjpassauxpassnpadvmodprep': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTdobjdetnummodpreppobjauxnsubj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTauxpasspreppcompdetnsubjpassappos': [[0, 0, 0, 0, 0, 2], [1, 0, 1, 0, 0, 0]],
  'ROOTprepdobjdetauxnsubjdobj': [[0, 0, 0, 1], [0, 1, 0, 0]],
  'ROOTattrdetauxnsubj': [[0, 0, 0, 0, 1], [0, 1, 0, 0, 0]],
  'ROOTnsubjdetattr': [[0, 0, 0, 2], [0, 2, 0, 0]],
  'ROOTauxnsubjpreppobjacomppreppobj': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTpobjnsubjpassauxpasspreppobj': [[0, 0, 0, 0, 1], [0, 0, 1, 0, 0]],
  'ROOTauxnsubjdobj': [[0, 0, 1, 0], [0, 0, 0, 1]],
  'ROOTdobjpreppobjpreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjdobjpreppobjprep': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTauxnsubjdetnsubj': [[0, 0, 0, 1], [0, 0, 1, 0]],
  'ROOTauxpasspreppcompdetnegadvmod': [[0, 0, 0, 0, 2, 0], [1, 0, 1, 0, 0, 0]],
  'ROOTnsubjdetccompnsubj': [[0, 0, 0, 2], [0, 1, 1, 0]],
  'ROOTnsubjpassauxpasspreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjpassdetauxpassagentpobjadvcl': [[0, 0, 0, 2, 0], [2, 0, 0, 0, 0]],
  'ROOTpobjnsubjpassauxpassadvmodpreppcompdobj': [[0, 0, 0, 0, 0, 0, 1], [0, 0, 1, 0, 0, 0, 0]],
  'ROOTnsubjnsubjpreppobj': [[0, 0, 1, 0], [0, 0, 0, 1]],
  'ROOTnsubjdobjpreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTdobjnsubjauxnsubj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjdetacomppreppobj': [[0, 0, 0], [0, 0, 0]],
  'ROOTnsubjpassdetauxpassdativepobjrelclnsubjauxnegdobj': [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]],
  'ROOTpreppobjdetnsubjnsubj': [[0, 0, 2, 0], [0, 2, 0, 0]],
  'ROOTnsubjattraclagent': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTadvcladvmodpreppobjcasensubjdobjacloprdattrnsubj': [[0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0]],
  'ROOTattrnsubjapposaclprep': [[0, 0, 0, 1, 0], [0, 0, 0, 0, 1]],
  'ROOTnsubjnsubjaclprep': [[0, 0, 4, 0], [0, 0, 0, 4]],
  'ROOTattrattrnummodpreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjpassdetauxpasspreppobjcase': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTnsubjdetpreppobj': [[0, 0, 0], [0, 0, 0]],
  'ROOTnsubjccompnpadvmodprep': [[0, 0, 0, 2], [0, 0, 2, 0]],
  'ROOTpreppobjccompnsubj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTauxpobjauxneg': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTnsubjnsubjprep': [[0, 0, 0], [0, 0, 0]],
  'ROOTnsubjdetauxnsubjpreppobjprep': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTpobjnsubjacomp': [[0, 0, 0], [0, 0, 0]],
  'ROOTprepnpadvmoddetattracl': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTdetadvmoddobjprep': [[0, 0, 2], [2, 0, 0]],
  'ROOTadvmodauxpassoprd': [[2, 0, 0, 0], [0, 2, 0, 0]],
  'ROOTattrattracladvcladvmoddobj': [[0, 0, 0, 0, 0, 0, 1], [0, 0, 1, 0, 0, 0, 0]],
  'ROOTadvmodauxpassadvmod': [[0, 0, 0, 2], [1, 1, 0, 0]],
  'ROOTdobjdetnsubjauxprep': [[0, 0, 0, 6, 0], [3, 3, 0, 0, 0]],
  'ROOTdetpreppobjaclpreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTdobjdetauxnsubj': [[0, 0, 0, 10, 10], [3, 17, 0, 0, 0]],
  'ROOTadvmodaux': [[0, 0], [0, 0]],
  'ROOTadvmodauxpassnpadvmodnmod': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTattrnsubjpreppobjrelclnsubjdobj': [[0, 0, 0, 0, 0, 2], [0, 0, 0, 1, 1, 0]],
  'ROOTnsubjnsubjapposprep': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTattrnsubjaclprep': [[0, 0, 9, 0], [0, 0, 0, 9]],
  'ROOTadvmodnsubj': [[0, 0, 0], [0, 0, 0]],
  'ROOTnsubjpassauxpasspreppcompdet': [[0, 2, 0, 0, 0], [2, 0, 0, 0, 0]],
  'ROOTattrnsubjpreppobjrelclpobjnsubjpassauxpassprep': [[0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0]],
  'ROOTattrnsubjpreppcompdobj': [[0, 0, 0, 1, 1], [0, 0, 2, 0, 0]],
  'ROOTpobjauxnsubjprep': [[0, 0, 0, 56], [29, 27, 0, 0]],
  'ROOTdobjauxnsubjpreppobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTadvmodauxnsubjdobjpreppobj': [[0, 0, 0, 0, 1], [0, 0, 0, 1, 0]],
  'ROOTpreppobjattracl': [[0, 0, 1, 0], [0, 0, 0, 1]],
  'ROOTadvmodauxpassnsubjappos': [[0, 0, 0, 0, 2], [1, 1, 0, 0, 0]],
  'ROOTprepnsubjdetattracl': [[0, 0, 0, 1, 0], [0, 1, 0, 0, 0]],
  'ROOTattrnsubjpreppcomp': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTauxdobjxcompauxpasspreppobj': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTnsubjdetattrprep': [[0, 0, 0], [0, 0, 0]],
  'ROOTpobjauxnsubjnsubjprep': [[0, 0, 0, 4], [2, 2, 0, 0]],
  'ROOTpreppcompdetauxdobj': [[2, 0, 0, 1, 0], [1, 1, 0, 0, 1]],
  'ROOTpobjnsubjnummod': [[0, 0, 0], [0, 0, 0]],
  'ROOTpobjnsubjaclprep': [[0, 0, 3, 0], [0, 0, 0, 3]],
  'ROOTattrdetattrprtprep': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTdobjnsubjpassauxpassadvmodpreppobj': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTdobjnsubjxcompauxdobjpreppobj': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTdobjnsubjdobj': [[0, 0, 0, 1], [0, 0, 1, 0]],
  'ROOTadvmodnsubjpasspreppobjauxpassagentpobj': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTprepdobjdetpreppobjauxnsubj': [[0, 0, 0, 0, 1], [0, 1, 0, 0, 0]],
  'ROOTadvcladvmodauxnsubjdobjnummod': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTauxpassadvmodnsubj': [[0, 0, 0, 2], [0, 0, 2, 0]],
  'ROOTattrnsubjpreppobjccompnsubjpreconjattrprep': [[0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0]],
  'ROOTadvcladvmodnsubj': [[0, 0, 0, 2], [1, 0, 1, 0]],
  'ROOTnsubjdobjappos': [[0, 0, 0, 1], [1, 0, 0, 0]],
  'ROOTauxdobjpreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTauxpassadvmodnegadvmod': [[0, 0, 0, 2, 0], [0, 0, 2, 0, 0]],
  'ROOTdobjdetpreppobjauxnsubjnsubj': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTpcompnsubjnsubjattr': [[0, 0, 2, 0], [0, 0, 0, 2]],
  'ROOTattr': [[0, 0], [0, 0]],
  'ROOTauxpassnpadvmodoprd': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTpreppobjnsubjnsubj': [[0, 0, 1, 0], [0, 0, 0, 1]],
  'ROOTdobj': [[0, 0], [0, 0]],
  'ROOTpobjattraclprep': [[0, 0, 3, 0], [0, 0, 0, 3]],
  'ROOTnsubjpassauxpassadvmodagent': [[0, 0, 0, 2], [2, 0, 0, 0]],
  'ROOTdobjnummodpreppobj': [[0, 0, 1], [0, 1, 0]],
  'ROOTpreppobjpreppobjpobjauxnsubjdobj': [[1, 0, 0, 0, 1], [0, 0, 2, 0, 0]],
  'ROOTpreppobjauxnsubjxcompauxdobj': [[0, 0, 0, 0, 1], [0, 1, 0, 0, 0]],
  'ROOTnsubjattrpreppobjdet': [[0, 2, 0, 0, 0], [0, 0, 1, 1, 0]],
  'ROOTnsubjccompnsubjprt': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTdobjpobjnsubjaux': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTprepnsubjdetnsubjapposdobj': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTattrdetattracl': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTdobjnsubjpassauxpasspreppcompdobj': [[0, 0, 0, 0, 0, 1], [0, 0, 1, 0, 0, 0]],
  'ROOTdobjrelclnsubjauxpreppobj': [[0, 0, 0, 1, 0, 0], [0, 1, 0, 0, 0, 0]],
  'ROOTauxnsubjdetnsubjneg': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTnsubjaux': [[0, 0, 0], [0, 0, 0]],
  'ROOTrelclpobjauxnsubjprep': [[2, 0, 0, 0], [0, 1, 1, 0]],
  'ROOTnsubjpasscaseauxpassadvmodprep': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTauxnsubjnmoddobjpreppobj': [[0, 0, 0, 2, 0, 0], [0, 0, 0, 0, 1, 1]],
  'ROOTnsubjdetacompadvmodpreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTattrccompnsubjacladvmodadvmodprep': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTnsubjadvmodauxprep': [[0, 9, 0, 0], [5, 0, 4, 0]],
  'ROOTnsubjadvmodattrpreppobj': [[0, 0, 0], [0, 0, 0]],
  'ROOTattrnsubjrelcladvmodnsubjpassauxpassadvcl': [[0, 0, 0, 0, 0, 2, 0, 0], [0, 0, 1, 0, 1, 0, 0, 0]],
  'ROOTadvmodauxpassnsubjpasscase': [[0, 0, 0, 2], [1, 1, 0, 0]],
  'ROOTattrnsubjapposprep': [[0, 0, 1, 0], [0, 0, 0, 1]],
  'ROOTpcompdobjnsubjauxnsubj': [[0, 0, 0, 0, 2], [2, 0, 0, 0, 0]],
  'ROOTexplattraclpreppobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTnsubjpassdetpreppobjauxpassadvmodpreppobj': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
  'ROOTccompnsubjauxnsubj': [[0, 2, 0, 0, 0], [2, 0, 0, 0, 0]],
  'ROOTnsubjprtpreppobj': [[0, 0, 0], [0, 0, 0]],
  'ROOTnsubjpasspreppobjauxpasspreppobjdet': [[0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 1, 0]],
  'ROOTauxpassauxoprd': [[0, 0, 0, 0], [0, 0, 0, 0]],
}
