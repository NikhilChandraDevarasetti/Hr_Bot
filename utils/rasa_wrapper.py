import os
from urllib.parse import urljoin
import requests
import json
from . import config


class RasaAPIWarapper:

    YAML_HEADER = {
        "Content-Type": "application/yaml"
    }
    JSON_HEADER = {
        "Content-Type": "application/json"
    }

    def train(self, data):

        status = False
        model_name = ""
        url = urljoin(config.BASE_URL, 'model/train')
        resp = requests.post(url, data=data, headers=self.YAML_HEADER)
        if resp.status_code == 200:
            model_name = resp.headers['filename']
            status = True
        return status, model_name

    def test(self):
        print("test")

    def replace_model(self, model_file):
        status = False
        url = urljoin(config.BASE_URL, 'model')
        data = json.dumps({
            "model_file": 'models/' + model_file
        })
        resp = requests.put(url, data=data, headers=self.JSON_HEADER)
        if resp.status_code == 204:
            status = True
        return status

    def replace_model_welcome(self, model_file):
        status = False
        url = urljoin(config.PROD_URL, 'model')
        data = json.dumps({
            "model_file": 'prod_models/' + model_file
        })
        resp = requests.put(url, data=data, headers=self.JSON_HEADER)
        if resp.status_code == 204:
            status = True
        return status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return
