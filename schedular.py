import os
import shutil
from utils.db_connector import db_connection
from datetime import datetime
from utils import rasa_wrapper as rasa_wrapper
from utils.create_dataset import get_training_set
import schedule
import time
from utils.logger import logger

event_logger = logger()


def fetch_nlu_id():
    my_collection = db_connection["nlu_data"]
    all_db_intents = my_collection.find({}, {"nlu_id": 1})
    nlu_data = []
    for nlu_ids in all_db_intents:
        nlu_data.append((nlu_ids["nlu_id"]))
    nlu_id = []
    for x in nlu_data:
        nlu_id.append(x)
    return nlu_id


def train_schedule_data():
    event_logger.info("Training model.")
    my_collection = db_connection["train_data"]
    my_collection_sc = db_connection["training_schedule"]
    up_intent_collection = db_connection["nlu_data"]
    all_count = my_collection_sc.count_documents({"status": "1"})
    if all_count > 0:
        all_db_intents = my_collection_sc.find({"status": "1"}).sort("_id", -1).limit(1)
        all_intents = []
        for x in all_db_intents:
            all_intents.append(x["model_id"])
        model_id = all_intents[0]
        training_data = get_training_set()
        with rasa_wrapper.RasaAPIWarapper() as rasaApi:
            status, model_name = rasaApi.train(data=training_data)
            if status == True:
                flag = "1"
                src = os.getcwd() + "/bot/models/" + model_name
                dst = os.getcwd() + "/bot/prod_models/" + model_name
                shutil.copyfile(src, dst)
                shutil.copy(src, dst)
                nlu_ids = fetch_nlu_id()
                prod_active_count = up_intent_collection.count_documents({"p_status": "1"})
                prod_inactive_count = up_intent_collection.count_documents(
                    {"p_status": "0"}
                )
                active_count = up_intent_collection.count_documents({"s_status": "1"})
                inactive_count = up_intent_collection.count_documents({"s_status": "0"})
                mydict = {
                    "$set": {
                        "model_name": model_name,
                        "timestamp": datetime.utcnow().isoformat(),
                        "intent_list": nlu_ids,
                        "status": flag,
                        "deploy": "0",
                        "prod_active_count": prod_active_count,
                        "prod_inactive_count": prod_inactive_count,
                        "active_count": active_count,
                        "inactive_count": inactive_count,
                    }
                }
                model_id_data = {"model_id": model_id}
                _id = my_collection.update_one(model_id_data, mydict)
                update_intent_data = {
                    "$set": {
                        "status": flag,
                    }
                }
                _id = up_intent_collection.update_many({}, update_intent_data)
                sch_mydict = {
                    "$set": {
                        "model_name": model_name,
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": "0",
                    }
                }
                model_id_data = {"model_id": model_id}
                _id = my_collection_sc.update_one(model_id_data, sch_mydict)
            else:
                active_count = up_intent_collection.find(
                    {"status": {"$in": ["2", "3", "5"]}}, {"nlu_id": 1}
                )
                all_intents = []
                for x in active_count:
                    all_intents.append(x["nlu_id"])
                untrained_intent_list = all_intents
                flag = "2"
                up_intent_collection.update_many(
                    {"nlu_id": {"$in": untrained_intent_list}},
                    {"$set": {"s_status": flag}},
                    True,
                )
                model_id_data = {"model_id": model_id}
                my_collection.delete_one(model_id_data)
    return True


schedule.every(1).minutes.do(train_schedule_data)
while True:
    schedule.run_pending()
    time.sleep(1)
