from pymongo import MongoClient


def db_connect(host="localhost", port="27017") -> MongoClient:
    client = MongoClient(f"mongodb://{host}:{port}/")  # при работе с контейнером MongoClient(f"mongo_db:27017")

    return client
