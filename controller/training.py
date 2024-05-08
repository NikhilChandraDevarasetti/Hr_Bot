from flask import (
    render_template,
    request,
    session,
    redirect,
    Blueprint,
    Response,
    url_for,
)
from utils.create_dataset import get_training_set
from utils import logger, rasa_wrapper as rasa_wrapper
from utils.db_connector import db_connection
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from utils import db_handler
import pandas as pd
import threading
import shutil
import os
from utils import config

training_details = Blueprint("training", __name__)
event_logger = logger.logger()


@training_details.route("/training_status")
def training_status():
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/400.html")

    try:
        if "3" not in session.get("access"):
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/401.html")
    session["status"] = "training"
    try:
        all_intents = db_handler.fetch_training_model()
        _all_intents = []

        for idx, x in enumerate(all_intents):
            _all_intents.append(
                [
                    idx + 1,
                    x.get("model_profile_name"),
                    x.get("status"),
                    pd.to_datetime(x.get("timestamp")),
                    x.get("trained_by"),
                    x.get("model_name"),
                    x.get("deploy"),
                    x.get("_id"),
                    active_count_test(x.get("model_id"), "1", "stage"),
                    active_count_test(x.get("model_id"), "0", "stage"),
                    active_count_test(x.get("model_id"), "1", "prod"),
                    active_count_test(x.get("model_id"), "0", "prod"),
                    x.get("model_id"),
                    x.get("approve_status"),
                ]
            )

        all_intents_approved = db_handler.fetch_approved_model()
        _all_intents_approved = []
        for idx, y in enumerate(all_intents_approved):
            _all_intents_approved.append(
                [
                    idx + 1,
                    y.get("model_profile_name"),
                    y.get("status"),
                    pd.to_datetime(y.get("timestamp")),
                    y.get("trained_by"),
                    y.get("model_name"),
                    y.get("deploy"),
                    y.get("_id"),
                    active_count_test(y.get("model_id"), "1", "stage"),
                    active_count_test(y.get("model_id"), "0", "stage"),
                    active_count_test(y.get("model_id"), "1", "prod"),
                    active_count_test(y.get("model_id"), "0", "prod"),
                    y.get("model_id"),
                    y.get("approve_status"),
                ]
            )
        train_collection = db_connection["train_data"]
        stag_model_count = train_collection.count_documents({"deploy": "2"})
        both_model_count = train_collection.count_documents({"deploy": "3"})
        total = stag_model_count + both_model_count
        return render_template(
            "admin/training.html",
            data=_all_intents,
            stag_model_count=total,
            approve_data=_all_intents_approved,
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@training_details.route("/pending_list")
def pending_list():
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/400.html")
    try:
        if "4" not in session.get("access"):
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    except Exception as e:
        return render_template("admin/401.html")
    try:
        session["status"] = "pending"
        all_intents = db_handler.fetch_pending_model()
        _all_intents = []
        for idx, x in enumerate(all_intents):
            _all_intents.append(
                [
                    idx + 1,
                    x.get("model_profile_name"),
                    x.get("status"),
                    pd.to_datetime(x.get("timestamp")),
                    x.get("trained_by"),
                    x.get("model_name"),
                    x.get("deploy"),
                    x.get("_id"),
                    active_count_test(x.get("model_id"), "1", "stage"),
                    active_count_test(x.get("model_id"), "0", "stage"),
                    active_count_test(x.get("model_id"), "1", "prod"),
                    active_count_test(x.get("model_id"), "0", "prod"),
                    x.get("model_id"),
                    x.get("approve_status"),
                ]
            )
        return render_template("admin/pending_training.html", data=_all_intents)
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@training_details.route("/model/train", methods=["POST"])
def train_model():
    """
    -- Check User Session
    -- Generate Model Id
    -- If Training Start Now
        -- Before Thread Start
            -- Update All intents those status is Untrained/Failed(2,3) to InProgress
            -- Create Document New Model Name without File
            -- Fetch Intent list and pass to view
        -- After Thread will Start
            -- Fetch all intents data from db
            -- Pass data to rasa for training
                -- if get status is success
                    -- move model file to anther folder(for run multiple rasa)
                    -- Update all Intent Status to Trained(1)
                    -- Update Model documents with New Generated model file and all Intent list
                -- else get status is failure
                    -- Changes the status of Untrained/Failed(2,3) Intents to TrainingFailed(4)
                    -- Delete Already created Document form database
    -- Else Training Scheduled
        -- Create New Model without File
        -- Add data in schedular collection with date
        -- Fetch Intent list and pass to view
    :return: Training View
    """
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/400.html")

    projectpath = request.form
    query_data = projectpath.to_dict(flat=False)
    user_model_name = query_data.pop("model_name")[0]
    r_status = query_data.pop("r_status")[0]
    s_date = query_data.pop("s_date")[0]
    result = {}
    result["status"] = "0"
    status_collection = db_connection["maintain_status"]
    evn_status = status_collection.count_documents(
        {"name": "stag_training_status", "status": "1"})
    if evn_status > 0:
        result["status"] = "1"
        return result
    try:
        my_collection = db_connection["train_data"]
        sc_collection = db_connection["training_schedule"]
        up_intent_collection = db_connection["nlu_data"]
        log_collection = db_connection["training_log"]
        model_profile = user_model_name
        ct = datetime.now()
        ts = ct.timestamp()
        model_id = str(int(ts))
        untrained_intents = db_handler.fetch_untrained_intents()
        rejected_intents = db_handler.fetch_rejected_intents()
        if r_status == "1":

            def long_running_task(**kwargs):
                event_logger.error(
                    "===================================================="
                )
                training_data = get_training_set()
                status_collection.update_one(
                    {"name": "stag_training_status"}, {"$set": {"status": "1"}}, True
                )
                with rasa_wrapper.RasaAPIWarapper() as rasaApi:
                    status, model_name = rasaApi.train(data=training_data)
                    event_logger.error(status)
                    if status == True:
                        flag = "1"
                        src = os.getcwd() + "/bot/models/" + model_name
                        dst = os.getcwd() + "/bot/prod_models/" + model_name
                        shutil.copyfile(src, dst)
                        shutil.copy(src, dst)
                        nlu_ids = db_handler.fetch_nlu_id()

                        prod_active_count = up_intent_collection.count_documents(
                            {"p_status": "1"})
                        prod_inactive_count = up_intent_collection.count_documents(
                            {"p_status": "0"})
                        active_count = up_intent_collection.count_documents(
                            {"s_status": "1"})
                        inactive_count = up_intent_collection.count_documents(
                            {"s_status": "0"})
                        mydict = {
                            "$set": {
                                "model_name": model_name,
                                "model_profile_name": model_profile,
                                "timestamp": datetime.utcnow().isoformat(),
                                "intent_list": nlu_ids,
                                "newly_train_intents": untrained_intents,
                                "status": flag,
                                "deploy": "0",
                                "prod_active_count": prod_active_count,
                                "prod_inactive_count": prod_inactive_count,
                                "active_count": active_count,
                                "inactive_count": inactive_count,
                                "approve_status": "0",
                            }
                        }
                        model_id_data = {"model_id": model_id}
                        _id = my_collection.update_one(model_id_data, mydict)
                        update_intent_data = {
                            "$set": {
                                "status": flag,
                            }
                        }
                        rejected_data = {"nlu_id": {"$ne": rejected_intents}}
                        _id = up_intent_collection.update_many(
                            rejected_data, update_intent_data
                        )
                        deploy_log = {
                            "model_name": model_name,
                            "model_id": model_id,
                            "timestamp": datetime.utcnow().isoformat(),
                            "status": "1",
                            "user": "neosoft",
                        }
                        _id = log_collection.insert_one(deploy_log)
                        s_id = deploy_stag(model_id)
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
                        deploy_log = {
                            "model_name": model_name,
                            "model_id": model_id,
                            "timestamp": datetime.utcnow().isoformat(),
                            "status": "2",
                            "user": "neosoft",
                        }
                        _id = log_collection.insert_one(deploy_log)
                status_collection.update_one(
                    {"name": "stag_training_status"}, {"$set": {"status": "0"}}, True
                )
                status_collection.update_one(
                    {"name": "intent_status"}, {"$set": {"status": "0"}}, True
                )

            thread = threading.Thread(
                target=long_running_task, kwargs={"post_data": projectpath}
            )
            thread.start()
            update_intent_data = {
                "$set": {
                    "status": "3",
                }
            }
            myquery_old = {"status": "2"}
            _id = up_intent_collection.update_many(myquery_old, update_intent_data)
            mydict_in = {
                "model_name": "",
                "model_profile_name": model_profile,
                "timestamp": datetime.utcnow().isoformat(),
                "model_id": model_id,
                "status": "3",
                "deploy": "5",
                "prod_active_count": "",
                "prod_inactive_count": "",
                "active_count": "",
                "inactive_count": "",
                "intent_list": [],
                "newly_train_intents": [],
                "approve_status": "0",
            }
            _id = my_collection.insert_one(mydict_in)
            all_intents = db_handler.fetch_all_intents()
            _all_intents = []

            for idx, x in enumerate(all_intents):
                _all_intents.append(
                    [
                        idx + 1,
                        x.get("intent"),
                        x.get("response"),
                        x.get("query"),
                        x.get("entities"),
                        x.get("timestamp"),
                        x.get("user"),
                        x.get("status"),
                        x.get("_id"),
                    ]
                )
            return render_template("admin/intent_table.html", data=_all_intents)
        else:
            mydict = {
                "model_name": "",
                "model_profile_name": model_profile,
                "timestamp": datetime.utcnow().isoformat(),
                "model_id": model_id,
                "status": "3",
                "deploy": "0",
                "intent_list": [],
                "newly_train_intents": [],
                "approve_status": "0",
            }
            _id = my_collection.insert_one(mydict)
            schedule_training = {
                "model_name": "",
                "model_profile_name": model_profile,
                "timestamp": datetime.utcnow().isoformat(),
                "schedule_time": s_date,
                "model_id": model_id,
                "status": "1",
            }
            _id = sc_collection.insert_one(schedule_training)
            update_intent_data = {
                "$set": {
                    "status": "4",
                }
            }
            _id = up_intent_collection.update_many({}, update_intent_data)
            all_intents = db_handler.fetch_all_intents()
            _all_intents = []
            for idx, x in enumerate(all_intents):
                _all_intents.append(
                    [
                        idx + 1,
                        x.get("intent"),
                        x.get("response"),
                        x.get("query"),
                        x.get("entities"),
                        x.get("timestamp"),
                        x.get("user"),
                        x.get("status"),
                        x.get("_id"),
                    ]
                )
            return render_template("admin/intent_table.html", data=_all_intents)
    except Exception as e:
        event_logger.error(e)
        return redirect(
            url_for("intent.display_intents", _external=True, _scheme=config.SSL_SECURITY)
        )


def deploy_stag(_model_id):
    try:
        id_ = _model_id
        my_collection = db_connection["train_data"]
        log_collection = db_connection["deploy_log"]
        all_db_intents = my_collection.find({"model_id": id_})
        all_intents = []
        for x in all_db_intents:
            all_intents.append(x["model_name"])
            all_intents.append(x["deploy"])
            all_intents.append(x["intent_list"])
        model_name = all_intents[0]
        deploy = all_intents[1]
        intent_list = all_intents[2]
        with rasa_wrapper.RasaAPIWarapper() as rasaApi:
            status = rasaApi.replace_model(model_file=model_name)
            if status == True:
                if deploy == "1":
                    status = "3"
                else:
                    status = "2"

                update_old_data_train = {
                    "$set": {
                        "deploy": "1",
                    }
                }
                myquery_old_train = {"deploy": "3"}
                my_collection_old = db_connection["train_data"]
                _id = my_collection_old.update_one(
                    myquery_old_train, update_old_data_train
                )

                update_nlu_data = {
                    "$set": {
                        "s_status": "0",
                    }
                }
                nlu_collection = db_connection["nlu_data"]
                _id = nlu_collection.update_many({}, update_nlu_data)
                nlu_collection.update_many(
                    {"nlu_id": {"$in": intent_list}}, {"$set": {"s_status": "1"}}, True
                )

                active_count = nlu_collection.count_documents({"s_status": "1"})
                inactive_count = nlu_collection.count_documents({"s_status": "0"})

                update_nlu_count = {
                    "$set": {
                        "active_count": active_count,
                        "inactive_count": inactive_count,
                    }
                }
                nlu_obj = {"model_id": id_}
                my_collection = db_connection["train_data"]
                _id = my_collection.update_many(nlu_obj, update_nlu_count)

                update_old_data = {
                    "$set": {
                        "deploy": "0",
                    }
                }
                myquery_old = {"deploy": "2"}
                my_collection_old = db_connection["train_data"]
                # print(str(myquery_old))
                _id = my_collection_old.update_one(myquery_old, update_old_data)

                update_intent_data = {
                    "$set": {
                        "deploy": status,
                    }
                }
                myquery = {"model_name": model_name}
                my_collection = db_connection["train_data"]
                _id = my_collection.update_one(myquery, update_intent_data)

                deploy_log = {
                    "model_name": model_name,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "1",
                    "environment": "staging",
                    "user": "neosoft",
                }
                _id = log_collection.insert_one(deploy_log)
            else:
                update_intent_data_tun = {
                    "$set": {
                        "deploy": "5",
                    }
                }
                myquery_run = {"model_name": model_name}
                my_collection = db_connection["train_data"]
                _id = my_collection.update_one(myquery_run, update_intent_data_tun)
                deploy_log = {
                    "model_name": model_name,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "2",
                    "environment": "staging",
                    "user": "neosoft",
                }
                _id = log_collection.insert_one(deploy_log)
        return _id
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@training_details.route("/replace/stag")
def replace_stag():
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/400.html")

    result = {}
    result["status"] = "0"
    try:
        status_collection = db_connection["maintain_status"]
        evn_status = status_collection.count_documents(
            {"name": "stag_training_status", "status": "1"})
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/400.html")

    if evn_status > 0:
        result["status"] = "1"
        return result
    id_ = request.args.get("id")
    my_collection = db_connection["train_data"]
    log_collection = db_connection["deploy_log"]
    all_db_intents = my_collection.find({"_id": ObjectId(id_)})
    all_intents = []
    for x in all_db_intents:
        all_intents.append(x["model_name"])
        all_intents.append(x["deploy"])
        all_intents.append(x["intent_list"])
    model_name = all_intents[0]
    deploy = all_intents[1]
    intent_list = all_intents[2]
    try:

        def long_running_task(**kwargs):
            status_collection.update_one(
                {"name": "stag_training_status"}, {"$set": {"status": "1"}}, True
            )
            with rasa_wrapper.RasaAPIWarapper() as rasaApi:
                status = rasaApi.replace_model(model_file=model_name)
                if status == True:
                    if deploy == "1":
                        status = "3"
                    else:
                        status = "2"

                    update_old_data_train = {
                        "$set": {
                            "deploy": "1",
                        }
                    }
                    myquery_old_train = {"deploy": "3"}
                    my_collection_old = db_connection["train_data"]
                    _id = my_collection_old.update_one(
                        myquery_old_train, update_old_data_train
                    )

                    update_nlu_data = {
                        "$set": {
                            "s_status": "0",
                        }
                    }
                    nlu_collection = db_connection["nlu_data"]
                    _id = nlu_collection.update_many({}, update_nlu_data)
                    nlu_collection.update_many(
                        {"nlu_id": {"$in": intent_list}},
                        {"$set": {"s_status": "1"}},
                        True,
                    )

                    active_count = nlu_collection.count_documents({"s_status": "1"})
                    inactive_count = nlu_collection.count_documents({"s_status": "0"})

                    update_nlu_count = {
                        "$set": {
                            "active_count": active_count,
                            "inactive_count": inactive_count,
                        }
                    }
                    nlu_obj = {"_id": ObjectId(id_)}
                    my_collection = db_connection["train_data"]
                    _id = my_collection.update_many(nlu_obj, update_nlu_count)

                    update_old_data = {
                        "$set": {
                            "deploy": "0",
                        }
                    }
                    myquery_old = {"deploy": "2"}
                    my_collection_old = db_connection["train_data"]
                    _id = my_collection_old.update_one(myquery_old, update_old_data)

                    update_intent_data = {
                        "$set": {
                            "deploy": status,
                        }
                    }
                    myquery = {"model_name": model_name}
                    my_collection = db_connection["train_data"]
                    _id = my_collection.update_one(myquery, update_intent_data)

                    deploy_log = {
                        "model_name": model_name,
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": "1",
                        "environment": "staging",
                        "user": "neosoft",
                    }
                    _id = log_collection.insert_one(deploy_log)
                else:
                    update_intent_data_tun = {
                        "$set": {
                            "deploy": "5",
                        }
                    }
                    myquery_run = {"model_name": model_name}
                    my_collection = db_connection["train_data"]
                    _id = my_collection.update_one(myquery_run, update_intent_data_tun)
                    deploy_log = {
                        "model_name": model_name,
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": "2",
                        "environment": "staging",
                        "user": "neosoft",
                    }
                    _id = log_collection.insert_one(deploy_log)
            status_collection.update_one(
                {"name": "stag_training_status"}, {"$set": {"status": "0"}}, True
            )

        thread = threading.Thread(
            target=long_running_task, kwargs={"post_data": model_name}
        )
        thread.start()
        # update_intent_data_tun = {
        #     "$set": {
        #         "deploy": "4",
        #     }
        # }
        # myquery_run = {"model_name": model_name}
        # my_collection = db_connection["train_data"]
        # _id = my_collection.update_one(myquery_run, update_intent_data_tun)
        all_intents = db_handler.fetch_training_model()
        _all_intents = []
        for idx, x in enumerate(all_intents):
            _all_intents.append(
                [
                    idx + 1,
                    x.get("model_profile_name"),
                    x.get("status"),
                    pd.to_datetime(x.get("timestamp")),
                    x.get("trained_by"),
                    x.get("model_name"),
                    x.get("deploy"),
                    x.get("_id"),
                    active_count_test(x.get("model_id"), "1", "stage"),
                    active_count_test(x.get("model_id"), "0", "stage"),
                    active_count_test(x.get("model_id"), "1", "prod"),
                    active_count_test(x.get("model_id"), "0", "prod"),
                    x.get("model_id"),
                    x.get("approve_status"),
                ]
            )
        return render_template("admin/training_table.html", data=_all_intents)
    except Exception as e:
        event_logger.error(e)
        return redirect(
            url_for("intent.display_intents", _external=True, _scheme=config.SSL_SECURITY)
        )


@training_details.route("/replace/prod")
def replace_model_prod():
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/400.html")
    result = {}
    result["status"] = "0"
    status_collection = db_connection["maintain_status"]
    evn_status = status_collection.count_documents(
        {"name": "prod_deploy_status", "status": "1"})
    if evn_status > 0:
        result["status"] = "1"
        return result
    else:
        id_ = request.args.get("id")
        my_collection = db_connection["train_data"]
        log_collection = db_connection["deploy_log"]
        all_db_intents = my_collection.find({"_id": ObjectId(id_)})
        all_intents = []
        for x in all_db_intents:
            all_intents.append(x["model_name"])
            all_intents.append(x["deploy"])
            all_intents.append(x["intent_list"])
        model_name = all_intents[0]
        deploy = all_intents[1]
        intent_list = all_intents[2]
        for x in all_db_intents:
            all_intents.append(x["model_name"])
            all_intents.append(x["deploy"])
        model_name = all_intents[0]
        deploy = all_intents[1]
        try:

            def long_running_task(**kwargs):
                status_collection.update_one(
                    {"name": "prod_deploy_status"}, {"$set": {"status": "1"}}, True
                )
                with rasa_wrapper.RasaAPIWarapper() as rasaApi:
                    status = rasaApi.replace_model_welcome(model_file=model_name)
                    if status == True:
                        if deploy == "2":
                            status = "3"
                        else:
                            status = "1"
                        update_old_data_train = {
                            "$set": {
                                "deploy": "2",
                            }
                        }
                        myquery_old_train = {"deploy": "3"}
                        my_collection_old = db_connection["train_data"]
                        _id = my_collection_old.update_one(
                            myquery_old_train, update_old_data_train
                        )
                        update_nlu_data = {
                            "$set": {
                                "p_status": "0",
                            }
                        }
                        nlu_collection = db_connection["nlu_data"]
                        _id = nlu_collection.update_many({}, update_nlu_data)
                        nlu_collection.update_many(
                            {"nlu_id": {"$in": intent_list}},
                            {"$set": {"p_status": "1"}},
                            True,
                        )
                        prod_active_count = nlu_collection.count_documents(
                            {"p_status": "1"})
                        prod_inactive_count = nlu_collection.count_documents(
                            {"p_status": "0"})

                        update_nlu_count = {
                            "$set": {
                                "prod_active_count": prod_active_count,
                                "prod_inactive_count": prod_inactive_count,
                            }
                        }
                        nlu_obj = {"_id": ObjectId(id_)}
                        my_collection = db_connection["train_data"]
                        _id = my_collection.update_many(nlu_obj, update_nlu_count)

                        update_old_data = {
                            "$set": {
                                "deploy": "0",
                            }
                        }
                        myquery_old = {"deploy": "1"}
                        my_collection_old = db_connection["train_data"]
                        _id = my_collection_old.update_one(myquery_old, update_old_data)

                        update_intent_data = {
                            "$set": {
                                "deploy": status,
                            }
                        }
                        myquery = {"model_name": model_name}
                        my_collection = db_connection["train_data"]
                        _id = my_collection.update_one(myquery, update_intent_data)

                        updated_values_all = {
                            "$set": {
                                "approve_status": "5",
                            }
                        }
                        queries_all = {"approve_status": "1"}
                        _id = my_collection.update_one(queries_all, updated_values_all)

                        updated_values = {
                            "$set": {
                                "approve_status": "1",
                            }
                        }
                        queries = {"model_name": model_name}
                        _id = my_collection.update_one(queries, updated_values)

                        deploy_log = {
                            "model_name": model_name,
                            "timestamp": datetime.utcnow().isoformat(),
                            "status": "1",
                            "environment": "production",
                            "user": "neosoft",
                        }
                        _id = log_collection.insert_one(deploy_log)
                    else:
                        update_intent_data_tun = {
                            "$set": {
                                "deploy": "5",
                            }
                        }
                        myquery_run = {"model_name": model_name}
                        my_collection = db_connection["train_data"]
                        _id = my_collection.update_one(
                            myquery_run, update_intent_data_tun
                        )
                        deploy_log = {
                            "model_name": model_name,
                            "timestamp": datetime.utcnow().isoformat(),
                            "status": "1",
                            "environment": "production",
                            "user": "neosoft",
                        }
                        _id = log_collection.insert_one(deploy_log)
                status_collection.update_one(
                    {"name": "prod_deploy_status"}, {"$set": {"status": "0"}}, True
                )

            thread = threading.Thread(
                target=long_running_task, kwargs={"post_data": model_name}
            )
            thread.start()
            # update_intent_data_tun = {
            #     "$set": {
            #         "deploy": "4",
            #     }
            # }
            # myquery_run = {"model_name": model_name}
            # my_collection = db_connection["train_data"]
            # _id = my_collection.update_one(myquery_run, update_intent_data_tun)

            all_intents = db_handler.fetch_training_model()
            _all_intents = []
            for idx, x in enumerate(all_intents):
                _all_intents.append(
                    [
                        idx + 1,
                        x.get("model_profile_name"),
                        x.get("status"),
                        pd.to_datetime(x.get("timestamp")),
                        x.get("trained_by"),
                        x.get("model_name"),
                        x.get("deploy"),
                        x.get("_id"),
                        active_count_test(x.get("model_id"), "1", "stage"),
                        active_count_test(x.get("model_id"), "0", "stage"),
                        active_count_test(x.get("model_id"), "1", "prod"),
                        active_count_test(x.get("model_id"), "0", "prod"),
                        x.get("model_id"),
                        x.get("approve_status"),
                    ]
                )
            return render_template("admin/training_table.html", data=_all_intents)
        except Exception as e:
            event_logger.error(e)
            return render_template("admin/500.html")


@training_details.route("/active_count_test")
def active_count_test(model_id, status, evn):
    try:
        my_collection = db_connection["train_data"]
        nlu_collection = db_connection["nlu_data"]
        all_db_intents = my_collection.find({"model_id": model_id}, {"intent_list": 1})
        all_intents = []
        if not all_db_intents:
            intent_list = []
        else:
            for x in all_db_intents:
                all_intents.append(x["intent_list"])
            intent_list = all_intents[0]
        nlu_data = ""
        if status == "1" and evn == "stage":
            nlu_data = nlu_collection.count_documents(
                {"s_status": "1", "nlu_id": {"$in": intent_list}})
        elif status == "0" and evn == "stage":
            nlu_data = nlu_collection.count_documents(
                {"s_status": "0", "nlu_id": {"$in": intent_list}})
        elif status == "1" and evn == "prod":
            nlu_data = nlu_collection.count_documents(
                {"p_status": "1", "nlu_id": {"$in": intent_list}})
        elif status == "0" and evn == "prod":
            nlu_data = nlu_collection.count_documents(
                {"p_status": "0", "nlu_id": {"$in": intent_list}})
        return str(nlu_data)
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@training_details.route("/view_intent", methods=["POST"])
def view_intent():
    try:
        projectpath = request.form
        query_data = projectpath.to_dict(flat=False)
        model_id = query_data.pop("model_id")[0]
        model_status = query_data.pop("status")[0]
        nlu_collection = db_connection["nlu_data"]
        my_collection = db_connection["train_data"]
        all_db_intents = my_collection.find({"_id": ObjectId(model_id)})
        all_intents = []
        for x in all_db_intents:
            all_intents.append(x["model_profile_name"])
            all_intents.append(x["deploy"])
            all_intents.append(x["intent_list"])
        model_name = all_intents[0]
        deploy = all_intents[1]
        intent_list = all_intents[2]
        nlu_data_intents = []
        if model_status == "1":
            model_status_intent = "Active Intents on Staging"
            nlu_data = nlu_collection.find(
                {"s_status": "1", "nlu_id": {"$in": intent_list}}, {"intent": 1}
            )
        elif model_status == "2":
            model_status_intent = "Inactive Intents on Staging"
            nlu_data = nlu_collection.find(
                {"s_status": "0", "nlu_id": {"$in": intent_list}}, {"intent": 1}
            )
        elif model_status == "3":
            model_status_intent = "Active Intents on Production"
            nlu_data = nlu_collection.find(
                {"p_status": "1", "nlu_id": {"$in": intent_list}}, {"intent": 1}
            )
        elif model_status == "4":
            model_status_intent = "Inactive Intents on Production"
            nlu_data = nlu_collection.find(
                {"p_status": "0", "nlu_id": {"$in": intent_list}}, {"intent": 1}
            )
        for x in nlu_data:
            nlu_data_intents.append(x["intent"])
        return render_template(
            "admin/intent_status.html",
            data=nlu_data_intents,
            model_name=model_name,
            model_status=model_status_intent,
        )
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@training_details.route("/change_status", methods=["POST"])
def change_status():
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/400.html")

    try:
        form_data = request.form.to_dict(flat=False)
        model_id = form_data.get("id")
        status = form_data.get("status")
        train_collection = db_connection["train_data"]
        if status[0] == "0" and session.get("role") == "2":
            updated_values = {
                "$set": {
                    "approve_status": "2",
                }
            }
            queries = {"model_id": model_id[0]}
            _id = train_collection.update_one(queries, updated_values)
        if status[0] == "2" and session.get("role") == "3":
            updated_values = {
                "$set": {
                    "approve_status": "1",
                }
            }
            queries = {"model_id": model_id[0]}
            _id = train_collection.update_one(queries, updated_values)
        all_intents = db_handler.fetch_training_model()
        _all_intents = []
        for idx, x in enumerate(all_intents):
            _all_intents.append(
                [
                    idx + 1,
                    x.get("model_profile_name"),
                    x.get("status"),
                    pd.to_datetime(x.get("timestamp")),
                    x.get("trained_by"),
                    x.get("model_name"),
                    x.get("deploy"),
                    x.get("_id"),
                    active_count_test(x.get("model_id"), "1", "stage"),
                    active_count_test(x.get("model_id"), "0", "stage"),
                    active_count_test(x.get("model_id"), "1", "prod"),
                    active_count_test(x.get("model_id"), "0", "prod"),
                    x.get("model_id"),
                    x.get("approve_status"),
                ]
            )
        return render_template("admin/training_table.html", data=_all_intents)
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@training_details.route("/reject_model", methods=["POST"])
def reject_model():
    try:
        if session.get("islogin") != 1:
            return redirect(url_for("auth.login", _external=True, _scheme=config.SSL_SECURITY))
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/400.html")
    try:
        form_data = request.form.to_dict(flat=False)
        model_id = form_data.get("id")
        status = form_data.get("status")
        train_collection = db_connection["train_data"]
        nlu_collection = db_connection["nlu_data"]
        if status[0] == "2":
            updated_values = {
                "$set": {
                    "approve_status": "4",
                }
            }
            queries = {"model_id": model_id[0]}
            _id = train_collection.update_one(queries, updated_values)

            all_db_intents = train_collection.find(
                {"model_id": model_id[0]}, {"newly_train_intents": 1}
            )
            all_intents = []
            if not all_db_intents:
                newly_train_intents = []
            else:
                for x in all_db_intents:
                    all_intents.append(x["newly_train_intents"])
                newly_train_intents = all_intents[0]
            nlu_collection.update_many(
                {"nlu_id": {"$in": newly_train_intents}},
                {"$set": {"status": "7"}},
                True,
            )
        all_intents = db_handler.fetch_training_model()
        _all_intents = []
        for idx, x in enumerate(all_intents):
            _all_intents.append(
                [
                    idx + 1,
                    x.get("model_profile_name"),
                    x.get("status"),
                    pd.to_datetime(x.get("timestamp")),
                    x.get("trained_by"),
                    x.get("model_name"),
                    x.get("deploy"),
                    x.get("_id"),
                    active_count_test(x.get("model_id"), "1", "stage"),
                    active_count_test(x.get("model_id"), "0", "stage"),
                    active_count_test(x.get("model_id"), "1", "prod"),
                    active_count_test(x.get("model_id"), "0", "prod"),
                    x.get("model_id"),
                    x.get("approve_status"),
                ]
            )
        return render_template("admin/training_table.html", data=_all_intents)
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")


@training_details.route("/revoke", methods=["POST"])
def revoke():
    try:
        projectpath = request.form
        query_data = projectpath.to_dict(flat=False)
        intent_list = list(query_data.get("intent_list[]")[0].split(" "))
        model_id = query_data.get("model_id")[0]
        nlu_collection = db_connection["nlu_data"]
        train_collection = db_connection["train_data"]
    except Exception as e:
        event_logger.error(e)
        return render_template("admin/500.html")
    try:
        nlu_collection.update_many(
            {"nlu_id": {"$in": intent_list}}, {"$set": {"status": "7"}}, True
        )
        train_collection.update_one(
            {"model_id": model_id}, {"$set": {"approve_status": "4"}}, True
        )
        all_intents = db_handler.fetch_training_model()
        _all_intents = []
        for idx, x in enumerate(all_intents):
            _all_intents.append(
                [
                    idx + 1,
                    x.get("model_profile_name"),
                    x.get("status"),
                    pd.to_datetime(x.get("timestamp")),
                    x.get("trained_by"),
                    x.get("model_name"),
                    x.get("deploy"),
                    x.get("_id"),
                    active_count_test(x.get("model_id"), "1", "stage"),
                    active_count_test(x.get("model_id"), "0", "stage"),
                    active_count_test(x.get("model_id"), "1", "prod"),
                    active_count_test(x.get("model_id"), "0", "prod"),
                    x.get("model_id"),
                    x.get("approve_status"),
                ]
            )
        return render_template("admin/training_table.html", data=_all_intents)
    except Exception as e:
        return "false"
