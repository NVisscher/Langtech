#!/usr/bin/python3

import time

import spacy
import requests

from SPARQLWrapper import SPARQLWrapper, JSON


def execute_query(x_id, y_id):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")

    sparql.setQuery("""SELECT DISTINCT  ?propertyLabel
               WHERE
                 {                                    
                   ?article  schema:about       ?item ;
                   schema:inLanguage  "en" ;
                   schema:isPartOf    <https://en.wikipedia.org/>
               FILTER ( ?item = <http://www.wikidata.org/entity/""" + str(y_id) + """>) 
        	   OPTIONAL { ?item rdfs:label ?itemLabel . FILTER (LANGMATCHES(LANG(?itemLabel),"EN"))  } .

                                      ?item wdt:""" + str(x_id) + """ ?property .
               SERVICE wikibase:label
                  { bd:serviceParam
                   wikibase:language  "en" 
                  }
               }""")

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    answer = []
    for result in results["results"]["bindings"]:
        answer.append(result["propertyLabel"]["value"])

    return answer


def get_entity_from_id(id):
    url = "https://www.wikidata.org/w/api.php"
    params = {"action": "wbgetentities", "ids": "" + id + "", "format": "json"}

    json = requests.get(url, params).json()
    return json


def search_entities(query):
    url = "https://www.wikidata.org/w/api.php"
    params = {"action": "wbsearchentities", "search": "" + query + "", "language": "en", "format": "json"}

    json = requests.get(url, params).json()
    return json


# Get the properties (and their labels) of an entity and match it against x.
def get_properties(x, y_id):
    properties = get_entity_from_id(y_id)

    # Get the labels of the properties.
    for property_id in properties["entities"][y_id]["claims"]:

        label = get_entity_from_id(property_id)

        # Return part of the URI if there is a match (P***).
        if x in label["entities"][property_id]["labels"]["en"]["value"]:
            return property_id

        if "aliases" in label["entities"][property_id]:
            if "en" in label["entities"][property_id]["aliases"]:
                if label["entities"][property_id]["aliases"]["en"] is not None:
                    # Check aliases if nothing was found.
                    for alias in label["entities"][property_id]["aliases"]["en"]:
                        if x in alias["value"]:
                            return property_id

        # This is not a Denial-of-Service attack tool. Give the servers some rest.
        time.sleep(0.55)

    # Cannot find property.
    return None


# Find items for y and get their properties.
def get_answer(x, y):
    items = search_entities(y)

    for item in items["search"]:
        x_id = get_properties(x, item["title"])

        if x_id is not None:
            # Return URIs when the answer was found.
            return [x_id, item["title"]]

    return None


# Find x and y, and make the input ready for further processing.
def pre_processor(input, nlp):
    doc = nlp(input)

    a = type1(doc)

    if len(a[0]) > 0 and len(a[1]) > 0:
        return [" ".join(a[0]).strip().lower(), " ".join(a[1]).strip().lower()]
    else:
        b = type2(doc)

        if len(b[0]) is not None and len(b[1]) is not None:
            return [b[0], b[1]]


def type1(doc):
    x = []
    y = []

    found_x = False
    found_y = False

    start_x = False
    start_y = False

    found_of_x = False

    for ent in doc:

        print(ent, ent.tag_)

        if found_x is False:
            if ent.tag_ == "NN" or ent.tag_ == "NNS" or ent.tag_ == "NNP":
                x.append(ent.text)

                start_x = True

            else:
                if ent.tag_ == "IN":

                    if found_of_x is False:

                        x.append(ent.text)
                        found_of_x = True
                    else:
                        found_x = True
        else:
            if start_x is True:
                found_x = True

        if found_y is False and found_x is True:
            if ent.tag_ == "IN" and len(y) is 0:
                continue

            if ent.tag_ == "NN" or ent.tag_ == "NNS" or ent.tag_ == "NNP" or ent.tag_ == "IN":
                y.append(ent.text)

                start_y = True
            else:
                if start_y is True:
                    found_y = True

    return [x, y]


def type2(doc):
    x = None
    y = None

    found_x = False

    for ent in doc:
        if (ent.tag_ == "NN" or ent.tag_ == "NNP" or ent.tag_ == "NNS" or ent.tag_ == "NNPS") and found_x:
            y = ent.text
        if (ent.tag_ == "NN" or ent.tag_ == "NNS" or ent.tag_ == "NNP") and not found_x:
            x = ent.text
            found_x = True

    return [x, y]


def get_answer_s3248216(question, nlp):
    try:
        input_stripped = question.strip()

        print(input_stripped)

        # Prepare values.
        x_y = pre_processor(input_stripped, nlp)

        if x_y is not None:

            # Find URIs for x (P****) and y (Q****).
            x_y_id = get_answer(x_y[0], x_y[1])

            if x_y_id is None:
                print("Could not find the answer on the question.\n")

                return []
            else:
                if len(x_y_id) == 2:
                    # Execute SPARQL query using the found URIs.
                    return execute_query(x_y_id[0], x_y_id[1])
                else:
                    print("An unknown error occurred.\n")

            # This is not a Denial-of-Service attack tool. Give the servers some rest.
            time.sleep(0.55)
        else:
            print("Could not extract x and/or y.\n")
            return []

    except FileNotFoundError:
        print("A questions.txt file was not found.")
        # except Exception:
        #   print("A fatal error occurred.")
