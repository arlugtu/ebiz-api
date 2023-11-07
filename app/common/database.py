from urllib.parse import quote_plus

from pymongo import MongoClient

from common.configs import MONGODB_PASSWORD, MONGODB_USERNAME, MONGODB_HOST, MONGODB_DB_NAME, MONGO_PORT
from common.logger import module_logger

logger = module_logger(__name__)


def get_mongo_client():
    """
    Get PyMongo Client object
    @return:
    """
    # password = quote_plus(MONGODB_PASSWORD)
    # url = f"mongodb://{MONGODB_USERNAME}:{password}@{MONGODB_HOST}:{MONGO_PORT}/?retryWrites=true&w=majority"
    url = f"mongodb://{MONGODB_HOST}:27017/?retryWrites=true&w=majority"
    client = MongoClient(url)
    return client


def get_collection(collection_name):
    """
    Connecting the database
    @return:
    """
    client = get_mongo_client()
    db = client[MONGODB_DB_NAME]
    collection = db[collection_name]
    logger.info(f'Database Connected for {collection_name}')
    return collection
