import ast
import json
import pymongo
import requests

class ActionHelper:

    def __init__(self, action_name):
        self.action_name = action_name
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db_connection = self.client["neobot"]
        self.mycol = self.db_connection["action_form"]
        self.data = self.mycol.find_one({'action_name': self.action_name})
        self.message_url = self.data.get("url")
        self.method_type = self.data.get("method_type")
        self.request_body = self.data.get("request_body")
        self.request_type = self.data.get("request_type")
        self.response_body = self.data.get("response_body")
        self.response_body = ast.literal_eval(self.response_body)
        self.headers = {"Content-type": "application/json"}

    def check_response(self):
        self.request_content = []
        self.final_response = []
        if self.method_type == "1" and len(self.request_body) > 0:
            request_dict = ast.literal_eval(self.request_body)
            request_params = ""
            for i in request_dict:
                param = i + "=" + str(request_dict[i]) + "&"
                request_params += param
            request_params = request_params.rstrip("&")
            request_url = self.message_url + "?" + request_params
            received_response = requests.get(request_url, headers=self.headers)
            self.request_content.append(received_response)

        if self.method_type == "1" and len(self.request_body) == 0:
            received_response = requests.get(self.message_url, headers=self.headers)
            self.request_content.append(received_response)

        if self.method_type == "2":
            request_dict = ast.literal_eval(self.request_body)
            request_params = ""
            for i in request_dict:
                param = i + "=" + str(request_dict[i]) + "&"
                request_params += param
            request_params = request_params.rstrip("&")
            request_url = self.message_url + "?" + request_params
            received_response = requests.post(request_url, headers=self.headers)
            self.request_content.append(received_response)
        self.response = json.loads(self.request_content[0].content)
        for i in self.response_body:
            if i in self.response:
                self.final_response.append(self.response[i])
        self.result = str(self.final_response[0])
        return self.request_type, self.result

