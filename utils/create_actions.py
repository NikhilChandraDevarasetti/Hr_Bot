from utils.db_connector import db_connection


class CustomActionGeneratior:
    """
    This is a class for mathematical operations on complex numbers.

    Attributes:
        action_file : The name of the action file .
    """

    def __init__(self, action_file):
        self.action_file = action_file
        self.action_file = open(self.action_file, 'w',encoding='utf-8')

    def read_data(self):
        '''
        Reads api data from mongo collection
        Returns: form data

       '''
        my_collection = db_connection["action_form"]
        self.form_data = my_collection.find()

    def package_importer(self):
        '''
        Writes static data to action file
        Returns: Action file

        '''
        self.read_data()

        package_imports = ["from typing import Any, Text, Dict, List \n",
                           "from rasa_sdk import Action, Tracker \n",
                           "from rasa_sdk.executor import CollectingDispatcher \n",
                           "from utils.action_helper import ActionHelper \n"]

        self.action_file.writelines(package_imports)
        self.action_file.writelines('\n')

        for i in self.form_data:
            intent = i['action_name'].split('_')[1]
            cls_name = 'Action' + str(intent)

            clas_name = 'class ' + cls_name + '(Action):'

            cls_name = [clas_name + '\n']
            self.action_file.writelines(cls_name)
            cs_name_new = 'action_' + str(intent)
            action_name = '\t\t' + 'return ' + '"' + str(cs_name_new) + '"'
            print(cs_name_new)

            defname = ['\tdef name(self) -> Text:\n',
                       action_name + '\n' + '\n']

            self.action_file.writelines(defname)

            defname, api_data = self.create_action()
            self.action_file.writelines(defname)
            self.action_file.writelines(api_data)

        self.action_file.close()

    def create_action(self):
        '''

        Creates a method for particular action
        Returns: API response & Action Name

        '''

        defname = [
            '\tdef run(self, dispatcher: CollectingDispatcher, tracker: Tracker,'
            ' domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:\n']

        api_data = ['\t\tac_name = self.name()\n',
                    '\t\taction_data = ActionHelper(ac_name)\n',
                    '\t\tself.request_type, self.result = action_data.check_response()\n\n'
                    '\t\tif self.request_type=="1":\n',
                    '\t\t\ttext = "Received respose is : " +self.result + "."\n',
                    '\t\t\tdispatcher.utter_message(text)\n', '\n',

                    '\t\tif self.request_type=="2":\n',
                    '\t\t\tdispatcher.utter_message(buttons = [{"payload": "/result", "title": "result"}])\n', '\n'
                    '\t\tif self.request_type=="3":\n',
                    '\t\t\tdispatcher.utter_message(attachment=self.result, json_message="video")\n', '\n',

                    '\t\tif self.request_type=="4":\n',
                    '\t\t\tdispatcher.utter_message(attachment=self.result, json_message="pdf")\n', '\n',

                    '\t\tif self.request_type=="5":\n',
                    '\t\t\tdispatcher.utter_message(image=self.result)\n',
                    '\t\treturn []\n', '\n']
        return defname, api_data

# data = CustomActionGeneratior('./actions/actions.py')
# data.package_importer()