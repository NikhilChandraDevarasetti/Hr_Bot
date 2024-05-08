from utils.db_connector import db_connection
from datetime import datetime
import pandas as pd
from bson.objectid import ObjectId
import re
import random
from flask import session
import threading


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


def insert_single_response(query_data):
    my_collection = db_connection["response_data"]
    query_data = query_data.to_dict(flat=False)
    description = (query_data.pop("description")[0])
    responses_type = (query_data.pop("responses_type")[0])
    responses_text = (query_data.pop("res_text")[0])
    response = []
    if responses_type == '1':
        x = []
        response.append("text")
        response.append(responses_text)
        for res in range(6):
            try:
                bt = []
                bt.append(query_data.pop("intentresponses_" + str(res))[0])
                x.append(bt)
            except Exception as e:
                break
        response.append(x)
    if responses_type == '2':
        x = []
        response.append("buttons")
        response.append(responses_text)
        for res in range(6):
            try:
                bt = []
                bt.append(query_data.pop("intentresponses_button_" + str(res))[0])
                bt.append(query_data.pop("intentresponses_payload_button_" + str(res))[0])
                x.append(bt)
            except Exception as e:
                break
        response.append(x)
    if responses_type == '3':
        x = []
        response.append("pdf")
        response.append(responses_text)
        for res in range(6):
            try:
                bt = []
                bt.append("pdf_attachment")
                bt.append("title")
                bt.append(query_data.pop("intentresponses_pdf_" + str(res))[0])
                x.append(bt)
            except Exception as e:
                break
        response.append(x)
    if responses_type == '4':
        x = []
        response.append("image")
        response.append(responses_text)
        for res in range(6):
            try:
                bt = []
                bt.append(query_data.pop("intentresponses_image_" + str(res))[0])
                x.append(bt)
            except Exception as e:
                break
        response.append(x)
    if responses_type == '5':
        x = []
        response.append("video")
        response.append(responses_text)
        for res in range(6):
            try:
                bt = []
                bt.append("video")
                bt.append(query_data.pop("intentresponses_video_" + str(res))[0])
                x.append(bt)
            except Exception as e:
                break
        response.append(x)
    ct = datetime.now()
    ts = ct.timestamp()
    res_time = int(ts)
    ran = random.randint(10, 40)
    res_id = str(res_time) + str(ran)
    mydict = {
        "response": response,
        "description": description,
        "status": "2",
        "res_id": str(res_id),
        "timestamp": datetime.utcnow().isoformat(),
        "user": "neosoft",
    }
    _id = my_collection.insert_one(mydict)
    return str(_id.inserted_id)
