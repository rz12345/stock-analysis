import firebase_admin
import json
import pandas as pd
from firebase_admin import credentials
from firebase_admin import db

class Firebase:    
    DB_URL = 'https://<YOUR-APP-NAME>.firebasedatabase.app/'
    CRED = credentials.Certificate("app/configs/firebase-cred.json")
    
    def updateNodeByCsv(node_ref, csv_file):
        csv_data = pd.read_csv(csv_file, dtype = {'stock_code': str})
        file_contents = csv_data.to_dict(orient='records')
        firebase_admin.initialize_app(__class__.CRED, {
            'databaseURL': __class__.DB_URL
        })
        db.reference(node_ref).set(file_contents)
        firebase_admin.delete_app(firebase_admin.get_app())
        
    def updateNodeByDict(node_ref, data):
        firebase_admin.initialize_app(__class__.CRED, {
            'databaseURL': __class__.DB_URL
        })
        db.reference(node_ref).set(data)
        firebase_admin.delete_app(firebase_admin.get_app())