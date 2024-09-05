from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['sql_app_mongo']
users_collection = db['users']
items_collection = db['items']
