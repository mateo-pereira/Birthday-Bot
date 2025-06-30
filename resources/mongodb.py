from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_CONN = os.getenv("DATABASE_URL")

class MongoDBConnection:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MongoDBConnection, cls).__new__(cls)
            cls._instance.client = MongoClient(DATABASE_CONN)
        return cls._instance

    def get_mongo_client(self):
        return self._instance.client

    def get_database(self, name):
        try:
            return self._instance.client[name]
        except Exception as e:
            print(e)
            return None
