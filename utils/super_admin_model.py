from utils.db_connector import db_connection
from datetime import datetime
import random

def fetch_all_user():
    """
    Fetch User List
    :return: User List(list)
    """
    admin_collection = db_connection["admin_login"]
    user_list = admin_collection.find({"status": { "$ne" : "0"}}).sort("_id", -1)
    return user_list


def insert_user(query_data):
    """
    Insert User
    :return: Insert User(list)
    """
    admin_collection = db_connection["admin_login"]
    query_data = query_data.to_dict(flat=False)
    name = query_data.pop("name")[0]
    username = query_data.pop("username")[0]
    role = query_data.pop("role")[0]
    email = query_data.pop("email")[0]
    ct = datetime.now()
    ts = ct.timestamp()
    nlu_time = int(ts)
    ran = random.randint(10, 40)
    admin_id = str(nlu_time) + str(ran)
    # password = name + "@" + str(ran)
    password = query_data.pop("password")[0]
    mydict = {
        "name": name,
        "username": username,
        "password": password,
        "role": role,
        "email": email,
        "status": "1",
        "reset_password": "0",
        "admin_id": str(admin_id),
        "timestamp": datetime.utcnow().isoformat(),
    }
    admin_collection.insert_one(mydict)

def update_user(query_data):
    """
    Update user Role basis of admin id
    :return: User Role(list)
    """
    admin_collection = db_connection["admin_login"]
    query_data = query_data.to_dict(flat=False)
    role = query_data.pop("role")[0]
    admin_id = query_data.pop("admin_id")[0]
    updated_values = {
        "$set": {
            "role": role,
        }
    }
    queries = {"admin_id": admin_id}
    _id = admin_collection.update_one(queries, updated_values)
    return _id

def fetch_all_role():
    """
    Fetch Role List
    :return: User Role(list)
    """
    admin_collection = db_connection["admin_role"]
    role_list = admin_collection.find().sort("_id", -1)
    return role_list


def admin_role_access(access):
    """
    All role related to particular user
    :return: String of all role
    """
    access_role = ""
    for all_access in access:
        if access_role != "":
            add = access_role + " , "
        else:
            add = access_role
        if all_access == "1":
            access_role = add + "Add Intent"
        if all_access == "2":
            access_role = add + "Intent List"
        if all_access == "3":
            access_role = add + "Training Status"
        if all_access == "4":
            access_role = add + "Pending List"
        if all_access == "5":
            access_role = add + "Intent Mapping"
        if all_access == "6":
            access_role = add + "All Chats"
        if all_access == "7":
            access_role = add + "Testing"
    return access_role

def insert_role(query_data):
    """
    Insert User
    :return: Insert User(list)
    """
    admin_collection = db_connection["admin_role"]
    query_data = query_data.to_dict(flat=False)
    name = query_data.pop("name")[0]
    access = query_data.pop("access[]")
    access_list = []
    for access_data in access:
        access_list.append(access_data)

    ct = datetime.now()
    ts = ct.timestamp()
    nlu_time = int(ts)
    ran = random.randint(10, 40)
    role_id = str(nlu_time) + str(ran)
    mydict = {
        "role": name,
        "access":access_list,
        "role_id":role_id
    }
    _id = admin_collection.insert_one(mydict)
    return _id


def update_role(query_data):
    """
    Update user Role basis of admin id
    :return: User Role(list)
    """
    admin_collection = db_connection["admin_role"]
    query_data = query_data.to_dict(flat=False)
    role_id = query_data.pop("role_id")[0]
    access = query_data.pop("access[]")
    access_list = []
    for access_data in access:
        access_list.append(access_data)
    updated_values = {
        "$set": {
            "access": access_list,
        }
    }
    queries = {"role_id": role_id}

    _id = admin_collection.update_one(queries, updated_values)

