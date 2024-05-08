import json
import pymongo
import os

from dotenv import load_dotenv
import os

load_dotenv()

MONGO_USER = os.getenv("MONGO_USER", None)
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", None)
MONGO_URI = os.getenv("MONGO_URI", None)
DB_NAME = os.getenv("DB_NAME", None)

connection_url = os.getenv("MONGO_URI")
path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "initdata", "db")
dir_list = os.listdir(path)

for i in dir_list:
    path_ = path + "/" + i
    with open(path_) as f:
        data = json.load(f)

    client = pymongo.MongoClient(connection_url)
    mydb = client["hrbot"]
    collection_name = i.split(".")[0]
    mycol = mydb[collection_name]

    x = mycol.insert_many(data)
