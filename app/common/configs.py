import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_PASSWORD = os.environ.get('MONGODB_PASSWORD')
MONGODB_USERNAME = os.environ.get('MONGODB_USERNAME')
MONGODB_HOST = os.environ.get('MONGODB_HOST')
MONGODB_DB_NAME = os.environ.get('MONGODB_DB_NAME')
LOG_LEVEL = os.environ.get('LOG_LEVEL')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
MONGO_PORT = os.environ.get('MONGO_PORT', '27017')
SELF_DOMAIN = os.environ.get('SELF_DOMAIN')
IS_DEBUG = os.environ.get('IS_DEBUG')
BOT_ENGINE_IMAGE = os.environ.get('BOT_ENGINE_IMAGE')
DOCKER_NETWORK = os.environ.get('DOCKER_NETWORK')
BOT_USERNAME = os.environ.get('BOT_USERNAME')
DNS_URL = os.environ.get('DNS_URL')
OXAPAY_MERCHANT = os.environ.get('OXAPAY_MERCHANT')
