from utils.db_connector import db_connection
from datetime import datetime
import pandas as pd
from bson.objectid import ObjectId
import re
import random
from flask import session
from werkzeug.utils import secure_filename
import os


UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath('./hrbot')), 'static/')


def fetch_all_stories():
    # my_collection = db_connection["custom_story"]
    my_collection = db_connection["custom_stories"]

    all_db_stories = my_collection.find()
    
    story_data = list(all_db_stories)
    story_list = []
    for one_story in story_data:
        story_list.append(one_story)
    return story_list

def fetch_all_actions():
    my_collection = db_connection["action_form"]

    all_actions = my_collection.find()

    action_data = list(all_actions)
    action_list = []
    for single_action in action_data:
        action_list.append(single_action)
    return action_list



def delete_single_story(query_data):
    story_collection = db_connection["custom_stories"]
    query_data = query_data.to_dict(flat=False)
    story_id = query_data.pop("id")[0]
    story_collection.delete_one({"_id":ObjectId(story_id)})
    return story_id


# need to update later for story
def update_single_story(projectpath):
    try:
        my_collection = db_connection["custom_stories"]

        query_data = dict(projectpath)
        steps_dict = []
        final_ = {}
        final_['story'] = query_data.pop('story_name')
        ids = query_data.pop("story_id")

        for one in query_data:
            if 'intent' in one:
                steps_dict.append({'intent':query_data[one]})
            else:
                steps_dict.append({'action':query_data[one]})
        final_['steps'] = steps_dict

        queries = {"_id": ObjectId(ids)}
        updated_values = {
            "$set": {
                "story": final_['story'],
                "steps": final_['steps'],
            }
        }
        _id = my_collection.update_one(queries, updated_values)
    except Exception as exp:
        print(exp)



def fetch_all_intents():
    my_collection = db_connection["nlu_data"]
    all_db_intents = my_collection.find({"status": { "$ne" : "8"}}).sort("_id", -1)
    return all_db_intents


def get_entities(input):
    all_entities = []
    for x in input:
        extracted_data = re.findall(r"\[+([[a-zA-z0-9@'.]+)]+\(([a-zA-Z]+)\)", x)
        entities = [
            all_entities.append(x[1])
            for x in extracted_data
            if x[1] not in all_entities
        ]

    return all_entities


def upload_n_store_file(storage_folder, file):
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(os.path.join(UPLOAD_FOLDER, storage_folder), filename)
        new_path = filepath.split('/static')[-1]
        new_path = 'http://127.0.0.1:6001/static'+new_path
        file.save(filepath)
    except Exception as e:
        print("error is ",e)
    return new_path


def insert_single_intent(query_data):
    try:
        query_data_form = query_data.form
        query_data_files = query_data.files
        my_collection = db_connection["nlu_data"]
        query_data_form = query_data_form.to_dict(flat=False)
        query_data_files = query_data_files.to_dict(flat=False)
        intent = query_data_form.pop("intent")[0].lower().replace(" ", "_")
        description = (query_data_form.pop("description")[0])
        title = (query_data_form.pop("title")[0])
        responses_type = (query_data_form.pop("responses_type")[0])
        
        if responses_type != '1':
            response_text = query_data_form.pop("res_text")[0]
        
        response = []
        if responses_type == '1':
            for res in range(6):
                try:
                    response.append(query_data_form.pop("intentresponses_" + str(res))[0])
                except Exception as e:
                    break
        if responses_type == '2':
            x = []
            response.append("buttons")
            response.append(response_text)
            for res in range(6):
                try:
                    bt = []
                    my_collection = db_connection["nlu_data"]
                    intent_title = my_collection.find({'intent': query_data_form.get("intentresponses_payload_button_" + str(res))[0]}, {'title': 1})
                    nlu_data = ''
                    for nlu_ids in intent_title:
                        nlu_data = (nlu_ids["title"])
                    bt.append(nlu_data)
                    bt.append(query_data_form.pop("intentresponses_payload_button_" + str(res))[0])
                    print(bt)
                    x.append(bt)
                except Exception as e:
                    break
            response.append(x)
        if responses_type == '3':
            x = []
            response.append("pdf")
            response.append(response_text)
            for res in range(6):
                try:
                    bt = []
                    bt.append(intent)
                    bt.append("this will be overwritten")
                    pdf_file = query_data_files["intentresponses_pdf_" + str(res)][0]
                    file_name_db = upload_n_store_file('pdfs', pdf_file)
                    print(file_name_db)
                    bt.append(file_name_db)
                    x.append(bt)
                except Exception as e:
                    break
            response.append(x)
        if responses_type == '4':
            x = []
            response.append("image") 
            response.append(response_text)
  
            for res in range(6):
                try:
                    bt = []
                    print("response text is ", response_text)
                    image_file = query_data_files["intentresponses_image_" + str(res)][0]
                    file_name_db = upload_n_store_file('images', image_file)
                    print("inserted file name",file_name_db)
                    bt.append(file_name_db)
                    x.append(bt)
                except Exception as e:
                    break
            response.append(x)
        if responses_type == '5':
            x = []
            response.append("video")
            response.append(response_text)

            for res in range(6):
                try:
                    bt = []
                    video_file = query_data_files["intentresponses_video_" + str(res)][0]
                    file_name_db = upload_n_store_file('videos', video_file)
                    print(file_name_db)
                    bt.append(file_name_db)
                    x.append(bt)
                except Exception as e:
                    break
            response.append(x)

        query = [_x[0] for _x in query_data_form.values()]
        entities = get_entities(query)
        ct = datetime.now()
        ts = ct.timestamp()
        nlu_time = int(ts)
        ran = random.randint(10, 40)
        nlu_id = str(nlu_time) + str(ran)
        syn_query = create_multiple_query(query)
        mydict = {
            "intent": intent,
            "response": response,
            "title": title,
            "description": description,
            "status": "2",
            "p_status": "0",
            "s_status": "0",
            "nlu_id": str(nlu_id),
            "query": query,
            "entities": entities,
            "timestamp": datetime.utcnow().isoformat(),
            "user": "neosoft",
            "syn_query": syn_query
        }
        _id = my_collection.insert_one(mydict)
        return str(_id.inserted_id)
    except Exception as e:
        print("error is ", e)


def get_synonyms(word):
    """
    find the synonyms of the given word
    Args:
        word(str): input word to get synonyms
    Returns:
            synonyms(list): list of synonyms of the given word
    """
    synonyms = []
    # for syn in wordnet.synsets(word):
    #     for l in syn.lemmas():
    #         synonyms.append(l.name())
    # return list(set(synonyms))
    return synonyms

def create_multiple_query(data_up):
    new_data = []
    for x in data_up:
        tokens = x.split(" ")
        new_data.append(x)
        for i, t in enumerate(tokens):
            syno = get_synonyms(t)
            if syno:
                for s in syno:
                    rest = (
                            " ".join(tokens[0:i])
                            + " "
                            + s
                            + " "
                            + " ".join(tokens[(i + 1): len(tokens)])
                    )
                    new_data.append(rest)
                    # print(type(intent[3]))
                    # my_collection.update_one({"nlu_id": "166728835731"}, {"$set": {"wordnet_queries": new_data}}, True)
    return new_data


def update_single_intent(query_data):
    my_collection = db_connection["nlu_data"]
    query_data = query_data.to_dict(flat=False)
    intent = query_data.pop("intent")[0]
    response = []
    for res in range(6):
        try:
            response.append(query_data.pop("intentresponses_" + str(res))[0])
        except Exception as e:
            break
    description = (query_data.pop("description")[0],)
    ids = query_data.pop("id")[0]
    nlu = query_data.pop("nlu_id")[0]
    query = [_x[0] for _x in query_data.values()]
    queries = {"_id": ObjectId(ids)}
    updated_values = {
        "$set": {
            "intent": intent,
            "response": response,
            "description": description,
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "2",
            "user": session.get("admin_id"),
        }
    }
    _id = my_collection.update_one(queries, updated_values)


def insert_multiple_intent(intent_file, schedule_time):
    my_collection = db_connection["nlu_data"]
    training_collection = db_connection["training_schedule"]
    intent_file = intent_file.to_dict(flat=False)
    intent_file = intent_file.get("intent_file")[0]
    df = pd.read_excel(intent_file, header=[0])
    if "intent" in df:
        df = df.groupby(["intent"])
    else:
        return "error"
    bulk_intents = dict(list(df))
    all_intents = bulk_intents.keys()
    _multiple_intents = []
    ct = datetime.now()
    ts = ct.timestamp()
    nlu_time = int(ts)
    for _intent in all_intents:
        my_collection.remove({'intent': _intent})
        _intents = _intent.lower().replace(" ", "_")
        ran = random.randint(10, 40)
        nlu_id = str(nlu_time) + str(ran)
        my_intent = bulk_intents.get(_intent)
        if "query" in my_intent:
            _queries = my_intent["query"].tolist()
        else:
            return "error"
        response = []
        title = ''
        if "response_type" in my_intent:
            if my_intent["response_type"].unique() == "buttons":
                x = []
                response.append("buttons")
                res_text = my_intent["response_text"].unique().tolist()
                response.append(res_text[0])
                for res in range(15):
                    try:
                        if len(my_intent["button_intent"][res]) == 0:
                            break
                        else:

                            title = my_intent["title"][res]
                            # bt.append(my_intent["button_intent"][res])
                            y = my_intent["button_intent"][res].split(",")
                            for i in y:
                                my_collection = db_connection["nlu_data"]
                                intent_title = my_collection.find(
                                    {'intent': i},
                                    {'title': 1})
                                bt = []
                                for nlu_ids in intent_title:
                                    nlu_title = (nlu_ids["title"])
                                    bt.append(nlu_title)
                                    bt.append(i)
                                x.append(bt)
                    except Exception as e:
                        pass
                response.append(x)
            if my_intent["response_type"].unique() == "pdf":
                response.append("pdf")
                for res_pdf in range(10):
                        try:
                            if len(my_intent["pdf_url"][res_pdf]) == 0:
                                break
                            else:
                                bt = []
                                bt.append("pdf_attachment")
                                bt.append("title")
                                bt.append(my_intent["pdf_url"][res_pdf])
                                x.append(bt)
                        except Exception as e:
                            break
            if my_intent["response_type"].unique() == "image":
                response.append("image")
                for res_image in range(10):
                    try:
                        if len(my_intent["image_url"][res_image]) == 0:
                            break
                        else:
                            bt = []
                            bt.append(my_intent["image_url"][res_image])
                            x.append(bt)
                    except Exception as e:
                        break
            if my_intent["response_type"].unique() == "video":
                response.append("video")
                for res_video in range(10):
                    try:
                        if len(my_intent["video_url"][res_video]) == 0:
                            break
                        else:
                            bt = []
                            bt.append("video")
                            bt.append(my_intent["video_url"][res_video])
                            x.append(bt)
                    except Exception as e:
                        break
            if my_intent["response_type"].unique() == "text":
                response.append("text")
                for res_text_data in range(10):
                    try:
                        if len(my_intent["text_response"][res_text_data]) == 0:
                            break
                        else:
                            bt = []
                            bt.append(my_intent["text_response"][res_text_data])
                            x.append(bt)
                    except Exception as e:
                        break
        _entities = get_entities(_queries)
        _multiple_intents.append(
            {
                "intent": _intents,
                "response": response,
                "title":title,
                "description": "Testing",
                "status": "2",
                "p_status": "0",
                "s_status": "0",
                "nlu_id": str(nlu_id),
                "query": _queries,
                "entities": _entities,
                "timestamp": datetime.utcnow().isoformat(),
                "user": "neosoft",
            }
        )
    my_collection.insert_many(_multiple_intents)

    # schedule training
    training_collection.insert_one(
        {"training_time": schedule_time, "user": "neosoft"})
    return "pass"


def fetch_training_model():
    my_collection = db_connection["train_data"]
    all_db_intents = my_collection.find({"$or":[{"deploy": {"$in":["1","2","3"]}},{"status":"3"}]}).sort("_id", -1)
    return all_db_intents

def fetch_approved_model():
    my_collection = db_connection["train_data"]
    all_db_intents = my_collection.find({"deploy": {"$nin":["1","2","3"]}}).sort("_id", -1)
    return all_db_intents


def fetch_pending_model():
    train_collection = db_connection["train_data"]
    all_pending_model = train_collection.find({"approve_status":"2"}).sort("_id", -1)
    return all_pending_model


def fetch_nlu_id():
    my_collection = db_connection["nlu_data"]
    all_db_intents = my_collection.find({'status': {"$ne" : "7"}},{'nlu_id':1})
    nlu_data = []
    for nlu_ids in all_db_intents:
        nlu_data.append((nlu_ids["nlu_id"]))
    nlu_id = []
    for x in nlu_data:
        nlu_id.append(x)
    return nlu_id


def fetch_untrained_intents():
    my_collection = db_connection["nlu_data"]
    all_db_intents = my_collection.find({'status':"2"}, {'nlu_id': 1})
    nlu_data = []
    for nlu_ids in all_db_intents:
        nlu_data.append((nlu_ids["nlu_id"]))
    nlu_id = []
    for x in nlu_data:
        nlu_id.append(x)
    return nlu_id


def fetch_rejected_intents():
    my_collection = db_connection["nlu_data"]
    all_db_intents = my_collection.find({'status':"7"}, {'nlu_id': 1})
    nlu_data = []
    for nlu_ids in all_db_intents:
        nlu_data.append((nlu_ids["nlu_id"]))
    nlu_id = []
    for x in nlu_data:
        nlu_id.append(x)
    return nlu_id


def admin_user(id):
    """
    Fetch User Name Using user ID
    :param id: user id(str)
    :return: User Name(str)
    """
    admin_collection = db_connection["admin_login"]
    user_data = admin_collection.find({"admin_id":id},{"name":1})
    admin_id = ""
    for admin_ids in user_data:
        admin_id = admin_ids["name"]
    return str(admin_id)


def fetch_mismatch_intent():
    map_collection = db_connection["fallback_queries"]
    all_db_intents = map_collection.find({"status":"0"}).sort("_id", -1)
    return all_db_intents


def delete_single_intent(query_data):
    nlu_collection = db_connection["nlu_data"]
    status_collection = db_connection["maintain_status"]
    query_data = query_data.to_dict(flat=False)
    nlu_id = query_data.pop("id")[0]
    _id = nlu_collection.update_one({"_id": ObjectId(nlu_id)}, {"$set": {"status": "8","updated_by": session.get("username"),
                                                                  "updated_date": datetime.utcnow().isoformat()}}, True)
    _id = status_collection.update_one({"name": "intent_status"}, {"$set": {"status": "1"}}, True)
    return _id


def delete_all_intent():
    nlu_collection = db_connection["nlu_data"]
    status_collection = db_connection["maintain_status"]
    _id = nlu_collection.update_many({"intent": {"$ne": "nlu_fallback"}}, {"$set": {"status": "8","updated_by": session.get("username"),
                                                                  "updated_date": datetime.utcnow().isoformat()}}, True)
    _id = status_collection.update_one({"name": "intent_status"}, {"$set": {"status": "1"}}, True)
    return _id


def insert_action_form(query_data):
    nlu_collection = db_connection["action_form"]
    try:
        query_data = query_data.to_dict(flat=False)
        userid = query_data.get('token')[0]
        pwd = query_data.get('token_value')[0]
        action_name = query_data.get('action_name')[0]
        url = query_data.get('url')[0]
        method_type = query_data.get('method')[0]
        request_type = query_data.get('request_type')[0]
        request_body = query_data.get('request')[0]
        response_body = query_data.get('response')[0]

        data = {'token':userid,'action_name':action_name,'token_value':pwd,'url':url,'method_type':method_type,'request_type':request_type,
                'request_body':request_body,'response_body':response_body}
        nlu_collection.insert_one(data)
    except Exception :
        pass


def delete_single_action(query_data):
    custom_actions = db_connection["action_form"]
    query_data = query_data.to_dict(flat=False)
    action_id = query_data.pop("id")[0]
    custom_actions.delete_one({"_id":ObjectId(action_id)})
    return action_id



def update_single_action(projectpath):
    my_collection = db_connection["action_form"]

    query_data = dict(projectpath)
    print(query_data)
    ids = query_data.get("custId")
    print(ids)
    token = query_data.get("token")
    print(token)
    action_name = query_data.get("action_name")
    print(action_name)
    token_value = query_data.get("token_value")
    url = query_data.get("url")
    method_type = query_data.get("method_type")
    request_type = query_data.get("request_type")
    request_body = query_data.get("request_body")
    response_body = query_data.get("response_body")

    queries = {"_id": ObjectId(ids)}
    updated_values = {
        "$set": {
            "token": token,
            "action_name": action_name,
            "token_value": token_value,
            "url": url,
            "method_type": method_type,
            "request_type": request_type,
            "request_body": request_body,
            "response_body": response_body
        }
    }


    _id = my_collection.update_one(queries, updated_values)