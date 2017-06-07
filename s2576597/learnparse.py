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

def skip(word):
  badwords = ['are', 'do', 'does', 'what', 'is', 'who', 'whom', 'why', 'can', "'s", 'was', 'did', 'get', 'give', 'have', 'has', 'there', 'how', 'also', 'be', 'list']
  if word in badwords:
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
  'ROOTccompnsubjauxnsubj': [[0, 1, 0, 0, 0], [1, 0, 0, 0, 0]],
  'ROOTnsubjattraclprep': [[0, 0, 3, 0], [0, 0, 0, 3]],
  'ROOTnsubjpassdetauxpasspreppobj': [[0, 0, 0, 0, 1], [0, 1, 0, 0, 0]],
  'ROOTattrdetpreppobjnsubj': [[0, 0, 0, 2], [0, 2, 0, 0]],
  'ROOTnsubjpassauxpassnsubjpassprep': [[0, 0, 0, 1], [1, 0, 0, 0]],
  'ROOTnsubjattr': [[0, 0, 0], [0, 0, 0]],
  'ROOTattrdetattrprtprep': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjpassauxpassxcompauxdobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTattrattrpreppobj': [[0, 0, 0, 2], [0, 0, 2, 0]],
  'ROOTnsubjpassauxpassadvmodagent': [[0, 0, 0, 1], [1, 0, 0, 0]],
  'ROOTauxnsubjdetnsubj': [[0, 0, 0, 0, 1], [0, 0, 1, 0, 0]],
  'ROOTnsubjattraclpreppobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTpobjauxnsubjprep': [[0, 0, 0, 3], [1, 2, 0, 0]],
  'ROOTpobjnsubjacomp': [[0, 0, 0], [0, 0, 0]],
  'ROOTnsubjpassauxpasspreppcompdet': [[0, 1, 0, 0, 0], [1, 0, 0, 0, 0]],
  'ROOTdobjdetauxnsubjxcompauxdobj': [[0, 0, 0, 0, 1], [0, 1, 0, 0, 0]],
  'ROOTnsubjdetdobj': [[0, 0, 0], [0, 0, 0]],
  'ROOTadvmodauxpassnsubjpass': [[0, 0, 0, 3], [1, 2, 0, 0]],
  'ROOTattrnsubjaclpreppobj': [[0, 0, 0, 0, 2], [0, 0, 2, 0, 0]],
  'ROOTpobjauxnsubjnsubjprep': [[0, 0, 0, 2], [1, 1, 0, 0]],
  'ROOTauxnsubjdobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTdobjpreppobj': [[0, 0, 4], [0, 4, 0]],
  'ROOTauxpassadvmodnsubjpass': [[0, 0, 0, 2], [1, 0, 1, 0]],
  'ROOTmarkauxpassnsubjnsubjpreppobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTnsubjacomp': [[0, 0], [0, 0]],
  'ROOTpobjauxnsubjdobjprep': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTattrnsubjpreppobj': [[0, 0, 0, 20], [0, 0, 20, 0]],
  'ROOTadvmodauxpassadvmod': [[0, 0, 0, 2], [1, 1, 0, 0]],
  'ROOTpobjnsubjpreppobj': [[0, 0, 0, 1], [0, 0, 1, 0]],
  'ROOTadvmodnsubjacl': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTpobjnsubjauxprep': [[0, 0, 4, 0], [2, 2, 0, 0]],
  'ROOTdetauxprep': [[0, 0, 0], [0, 0, 0]],
  'ROOTnsubjdobjcase': [[0, 0, 0], [0, 0, 0]],
  'ROOTpobjnsubjaclprep': [[0, 0, 1, 0], [0, 0, 0, 1]],
  'ROOTattrnsubjpreppobjpreppobj': [[0, 0, 0, 1, 13], [0, 0, 7, 7, 0]],
  'ROOTnsubjdetattrpreppobj': [[0, 0, 0, 0, 1], [0, 0, 0, 1, 0]],
  'ROOTadvmodauxnsubj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTauxpassauxoprd': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTpobjauxpassnpadvmodprep': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTadvmodauxpassoprd': [[1, 0, 0, 0], [0, 1, 0, 0]],
  'ROOTnsubjdobjdetauxprep': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTpobjdetnsubjauxprep': [[0, 0, 0, 2, 0], [1, 1, 0, 0, 0]],
  'ROOTnsubjpassdetauxpassxcompauxdobj': [[0, 0, 0, 0, 0, 1], [0, 1, 0, 0, 0, 0]],
  'ROOTnsubjdobj': [[0, 0, 3], [3, 0, 0]],
  'ROOTdobjdobjauxnsubj': [[0, 0, 0, 0, 1], [0, 0, 1, 0, 0]],
  'ROOTnsubjattraclagent': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTadvmodnsubj': [[0, 0, 0], [0, 0, 0]],
  'ROOTnsubjdetattraclprep': [[0, 0, 0, 1, 0], [0, 0, 0, 0, 1]],
  'ROOTdobjnsubjaux': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTpobjattraclprep': [[0, 0, 2, 0], [0, 0, 0, 2]],
  'ROOTattrnsubjpreppobjrelclpobjnsubjpassauxpassprep': [[0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0]],
  'ROOTnsubjattrpreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjnsubj': [[0, 0, 0], [0, 0, 0]],
  'ROOTnsubjnsubjattr': [[0, 0, 0], [0, 0, 0]],
  'ROOTpreppobjattracl': [[0, 0, 1, 0], [0, 0, 0, 1]],
  'ROOTadvmodnsubjauxprep': [[0, 0, 2, 0], [1, 1, 0, 0]],
  'ROOTdobjdetauxnsubj': [[0, 0, 0, 2, 2], [1, 3, 0, 0, 0]],
  'ROOTprepattrdetnsubj': [[0, 0, 0, 1], [0, 1, 0, 0]],
  'ROOTnsubjadvmodpreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTattrnsubjpreppobjcasepreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTadvmodauxnsubjdobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjpassdetauxpassagentpobj': [[0, 0, 0, 0, 1], [1, 0, 0, 0, 0]],
  'ROOTnsubjauxnsubj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjdetpreppobjattr': [[0, 0, 0, 1], [0, 1, 0, 0]],
  'ROOTnsubjpassdetauxpassagentpobjadvcl': [[0, 0, 0, 1, 0], [1, 0, 0, 0, 0]],
  'ROOTdobjauxnsubj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTnsubjattradvmodprep': [[0, 0, 0], [0, 0, 0]],
  'ROOTauxnsubjpassauxpasspreppobj': [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]],
  'ROOTnsubjnsubjaclprep': [[0, 0, 2, 0], [0, 0, 0, 2]],
  'ROOTadvcladvmodnsubjpass': [[0, 0, 0, 2], [1, 0, 1, 0]],
  'ROOTadvmodauxpassnpadvmod': [[0, 0, 0, 2], [1, 1, 0, 0]],
  'ROOTdobjauxnsubjnsubj': [[0, 0, 0, 0, 1], [0, 0, 0, 1, 0]],
  'ROOTattrcsubjnsubjpasspreppobjpreppobjnmodauxpassprep': [[0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]],
  'ROOTpreppobjdetnsubjnsubj': [[0, 0, 1, 0], [0, 1, 0, 0]],
  'ROOTattrnsubjaclprep': [[0, 0, 2, 0], [0, 0, 0, 2]],
  'ROOTprepdobjdetauxnsubj': [[0, 1, 0, 1], [1, 1, 0, 0]],
  'ROOTdobjdobjprep': [[0, 0, 0], [0, 0, 0]],
  'ROOTadvmodnsubjpreppobj': [[0, 0, 0, 4], [0, 2, 2, 0]],
  'ROOTnsubjccompnpadvmodprep': [[0, 0, 0, 1], [0, 0, 1, 0]],
  'ROOTpreppobjnsubjacl': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTdobjdetnsubjauxprep': [[0, 0, 0, 2, 0], [1, 1, 0, 0, 0]],
  'ROOTpobjdetauxnsubjprep': [[0, 0, 0, 0, 2], [1, 1, 0, 0, 0]],
  'ROOTnsubjpassauxpassxcompprep': [[1, 0, 0, 0], [0, 0, 0, 1]],
  'ROOTnsubjpassauxpasspreppobj': [[0, 0, 0, 0], [0, 0, 0, 0]],
  'ROOTattrattraclprep': [[0, 0, 2, 0], [0, 0, 0, 2]],
  'ROOTnsubjpassdetpreppobjauxpassadvmodpreppobj': [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
}
