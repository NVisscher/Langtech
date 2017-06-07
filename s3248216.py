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
    x = []
    y = None

    doc = nlp(input)

    found_x = False
    found_y = False

    for ent in doc:
        if (
                        ent.tag_ == "NN" or ent.tag_ == "NNP" or ent.tag_ == "NNS" or ent.tag_ == "NNPS") and found_x and not found_y:
            y = ent.text

            found_y = True
        if (ent.tag_ == "NN" or ent.tag_ == "NNS" or ent.tag_ == "NNP") and not found_x:
            x.append(ent.text)
            found_x = True

    if x is not None and y is not None:
        return [" ".join(x).strip().lower(), y.strip().lower()]
    else:
        return None


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
