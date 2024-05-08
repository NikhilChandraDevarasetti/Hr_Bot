"""
Converts training data into YAML format which is used to train rasa model
"""
from utils.db_connector import db_connection
import yaml
from typing import List
from utils.create_actions import CustomActionGeneratior

def call_custom_action():
    action = CustomActionGeneratior('./actions/actions.py')
    action.package_importer()


def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, str_presenter)
yaml.representer.SafeRepresenter.add_representer(str, str_presenter)


def fetch_intent():
    """Get intents from database and create list of intents

    Returns:
        list[str]: List of training intents fetched from database.
    """
    nlu_data = db_connection["nlu_data"].find({'status': {"$ne" : "7"}})  # nlu_data
    intents = [record["intent"] for record in nlu_data]
    return intents


def fetch_actions():
    """Get intents from database and create list of intents

    Returns:
        list[str]: List of training intents fetched from database.
    """
    nlu_data = db_connection["action_form"].find({'status': {"$ne" : "7"}})  # nlu_data
    actions = [record["action_name"] for record in nlu_data]
    return actions

def fetch_response():

    nlu_data = db_connection["nlu_data"].find()
    responses = {}
    for records in nlu_data:
        if records['response'][0]=='buttons':
            for i in records['response'][1:]:
                for j in i:
                    a = "utter_" + records["intent"]
                    if a not in responses:
                        responses[a] = [{"buttons": [{'title':j[0],'payload':j[1]}]}]
                    else:
                       responses[a][0]['buttons'].append({'title':j[0],'payload':j[1]})

        if records['response'][0]=='text':
            for i in records['response'][1:]:
                for j in i:
                    a = "utter_" + records["intent"]
                    if a not in responses:
                        responses[a] = [{"text":j}]
                    else:
                       responses[a][0]['text'].extend(j)

        # if records['response'][0]=='image':
        #     for i in records['response'][1:]:
        #         for j in i:
        #             a = "utter_" + records["intent"]
        #             if a not in responses:
        #                 responses[a] = [{"image":j}]
        #             else:
        #                responses[a][0]['image'].extend(j)


        if records['response'][0]=='video':
            for i in records['response'][1:]:
                for j in i:
                    a = "utter_" + records["intent"]
                    if a not in responses:
                        responses[a] = [{"attachment":{"type": "video","payload": {"src": j}}}]
                    else:
                       responses[a][0]['attachment'].extend({"type": "video","payload": {"src": j}})


        if records['response'][0]=='pdf':
            for i in records['response'][1:]:
                for j in i:
                    a = "utter_" + records["intent"]
                    if a not in responses:
                        responses[a] = [{"custom":{"payload": "pdf_attachment","url": j}}]
                    else:
                       responses[a][0]['custom'].extend({"payload": "pdf_attachment","url":j})

    return responses

def fetch_nlu():
    """Get NLU data from database. intents and its examples
    eg: [{"intent": "greet","examples": "- hey\n- hello\n- hi\n- hello there\n- hey there\n"}]

    Returns:
        List[Dict[str]]: intent and expected input query
    """
    nlu_data = db_connection["nlu_data"]     # nlu_data
    nlu_data = nlu_data.find()
    responses = {}
    nlu = []

    for records in nlu_data:
        query = ""
        responses["utter_" + records["intent"]
                  ] = [{"text": records["response"]}]
        query = ""
        for queries in records["query"]:
            query = query + "- " + queries + "\n"
        nlu.append({"intent": records["intent"], "examples": str(query)})
    return nlu


def construct_nlu_rules(input_intents: List[str]):
    """construct nlu rules
    eg:
    [{"rule": "description of rule/intent",
    "steps": [{"intent": "greet"}, {"action": "utter_greet"}]}

    Args:
        input_intents (List[str]): list of intents fetched from database

    Returns:
        List[Dict,Dict]: list of dictionaries containing intent and its response
    """
    constructed_rules = []
    for _intent in input_intents:
        single_rule = {}
        # static description for every intent
        single_rule["rule"] = "intent_desc"

        single_rule["steps"] = [{"intent": _intent},
                                {"action": f"utter_{_intent}"}]
        constructed_rules.append(single_rule)
    return constructed_rules


def fetch_temp_response():
    """Get intent responses from database and create list of dict containing responses
    eg: {'utter_intent': [{'text': 'sample_response'}]}

    Returns:
        Dict[List[Dict[str]]]: Dictionary containing list of intent response feteched from database
    """
    nlu_data = db_connection["nlu_data"].find({'status': {"$ne" : "7"}})
    responses = {}
    for records in nlu_data:
        if type(records["response"]) == str:
            responses["utter_" + records["intent"]] = [{"text": records["response"]}]
        else:
            responses["utter_" + records["intent"]] = []
            for i in records['response']:
                responses["utter_" + records["intent"]].append({"text": i})

    return responses


def fetch_stories():
    nlu_data = db_connection["nlu_data"]     # nlu_data
    nlu_data = nlu_data.find()
    intents = {}
    responses = {}
    data_steps = {}
    steps = []
    stories = []
    data_steps["story"] = "happy"
    for records in nlu_data:
        intents = {}
        responses = {}
        intents["intent"] = records["intent"]
        responses["action"] = "utter_" + records["intent"]
        steps.append(intents)
        steps.append(responses)
    data_steps["steps"] = steps

    # custom_story = db_connection["custom_story"]


    stories.append(data_steps)
    #print('stories',stories)


    return stories


def fetch_entities():
    """get entities from database

    Returns:
        List[str]: list of entities
    """
    nlu_data = db_connection["nlu_data"]     # nlu_data
    nlu_data = nlu_data.find()
    entities = []
    for records in nlu_data:
        if 'entities' in records:
            for entity in records['entities']:
                entities.append(entity)
    return entities


def fetch_slots():
    """_summary_

    Returns:
        _type_: _description_
    """
    nlu_data = db_connection["nlu_data"]     #nlu_data
    nlu_data = nlu_data.find()
    slots = {}

    for records in nlu_data:
        if 'entities' in records:
            for i in records['entities']:
                slots.update({i: {"type": "rasa.shared.core.slots.TextSlot",
                              "mappings": [
                                  {
                                      "type": "from_entity",
                                      "entity": i
                                  }
                              ]}})
    return slots




def fetch_custom_story():
    nlu_data = db_connection['custom_stories']
    nlu_data = nlu_data.find()
    stories = []
    for records in nlu_data:
        stories.append({'steps': records['steps'], 'story': records['story']})
    #print(stories)
    return stories



def get_training_set():
    pipeline = [
        {
            "name": "WhitespaceTokenizer"
        },
        {
            "name": "CountVectorsFeaturizer"
        },
        {
            "name": "DIETClassifier",
            "epochs": 200
        },
        {
            "name": "EntitySynonymMapper"
        },
        {
            "name": "ResponseSelector",
            "epochs": 200
        },
        {
            "name": "FallbackClassifier",
            "threshold": 0.8
        },
        {
            "name": "SpacyNLP",
            "model": "en_core_web_md"
        },
        {
            "name": "SpacyEntityExtractor"
        }

    ]
    policies = [
        {
            "name": "MemoizationPolicy",
            "max_history": 3
        },
        {
            "name": "TEDPolicy",
            "max_history": 5,
            "epochs": 200
        },
        {
            "name": "RulePolicy",
            "core_fallback_threshold": 0.4,
            "core_fallback_action_name": "action_default_fallback",
            "enable_fallback_prediction": True
        }
    ]
    intents = fetch_intent()
    entities = fetch_entities()
    slots = fetch_slots()
    actions = fetch_actions()

    forms = {}
    e2e_actions = []
    responses = fetch_temp_response()
    session_config = {
        "session_expiration_time": 60,
        "carry_over_slots_to_new_session": True,
    }

    rules = []        # construct_nlu_rules(intents)

    nlu = fetch_nlu()
    action = call_custom_action()

    stories = fetch_custom_story()



    data = {
        "version": "3.1",
        "recipe": "default.v1",
        "language": "en",
        "intents": intents,
        "entities": entities,
        "actions": actions,
        "slots": slots,
        "forms": forms,
        "e2e_actions": e2e_actions,
        "responses": responses,
        "session_config": session_config,
        "nlu": nlu,
        "rules": rules,
        "stories": stories,
        "pipeline": pipeline,
        "policies": policies
    }

    training_data = yaml.safe_dump(
        data, indent=2, default_flow_style=False, sort_keys=False
    )
    return training_data
