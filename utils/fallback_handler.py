from utils.db_connector import db_connection
from datetime import datetime, timedelta
import random


def fetch_chats():
    my_collection = db_connection["conversations"]
    chat_collection = db_connection['fallback_chats']
    data = my_collection.find({})
    query = []
    response = []
    intent = []
    count = 0
    for i in data:
        for j in i['events']:
            if 'text' in j:
                count = count + 1
                if count % 2 == 0:
                    response.append(j['text'])
                else:
                    query.append(j['text'])
            if 'name' in j and 'utter' in j['name']:
                intent.append(j['name'][6:])

    chats = []
    for queries, responses, intents in zip(query, response, intent):
        if len(queries) < 100:
            chats.append({'intent': intents, 'queries': queries, 'response': responses})
    chat_collection.insert_many(chats)
    return chats


def fetch_mismatch_chats():
    my_collection = db_connection["conversations"]
    chat_collection = db_connection['fallback_queries']
    data = my_collection.find({})
    query = []
    response = []
    intent = []
    count = 0
    for i in data:
        for j in i['events']:
            if 'text' in j:
                count = count + 1
                if count % 2 == 0:
                    response.append(j['text'])
                else:
                    query.append(j['text'])
            if 'name' in j and 'utter' in j['name']:
                intent.append(j['name'][6:])

    chats = []
    new_query = []
    fallback_data = list(chat_collection.find({},{'query':1,'_id':0}))
    fallback_queries = [one_query['query'] for one_query in fallback_data]
    for queries, responses, intents in zip(query, response, intent):
        q_id = ''
        ran = ''
        q_ids = ''
        if responses == "I'm sorry, I didn't quite understand that. Could you rephrase?" or responses == "I didn't understand you. Please select options mentioned below.":
            if queries not in fallback_queries:
                ct = datetime.now()
                ts = ct.timestamp()
                q_id = int(ts)
                ran = random.randint(100, 999)
                q_ids = str(q_id) + str(ran)
                chats.append({'query': queries, 'q_id': q_ids, 'status': '0'})
    if not chats:
        chats = []
    else:
        chat_collection.insert_many(chats)
    return chats
