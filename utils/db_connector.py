import pymongo
from . import config
from utils.logger import logger

event_logger = logger()
try:
    client = pymongo.MongoClient(config.MONGO_URI)
    db_connection = client[config.DB_NAME]

except (
    AttributeError,
    pymongo.errors.OperationFailure,
    pymongo.errors.ConnectionFailure,
) as e:
    event_logger.error(f"Error Connecting database: {e}")
