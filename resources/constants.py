from resources.mongodb import MongoDBConnection


mongo_connection = MongoDBConnection()
database = mongo_connection.get_database("Beast-Bot")
USERS = database["Users"]