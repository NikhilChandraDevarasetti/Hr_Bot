from dotenv import load_dotenv
import os

load_dotenv()
SSL_SECURITY = os.getenv("SSL_SECURITY", None)
MONGO_USER = os.getenv("MONGO_USER", None)
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", None)
MONGO_URI = os.getenv("MONGO_URI", None)
DB_NAME = os.getenv("DB_NAME", None)
BASE_URL = os.getenv("BASE_URL", None)
PROD_URL = os.getenv("PROD_URL", None)

SECRET_KEY = os.getenv("SECRET_KEY", None)
SESSION_TYPE = os.getenv("SESSION_TYPE", None)
REDIS_URL = os.getenv("REDIS_URI", None)

MAIL_SERVER = os.getenv("MAIL_SERVER", None)
MAIL_PORT = 2525
MAIL_USERNAME = os.getenv("MAIL_USERNAME", None)
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", None)
MAIL_USE_TLS = True
MAIL_USE_SSL = False

PROD_SOCKET_URI = os.getenv("PROD_SOCKET_URI", None)
STAGING_SOCKET_URI = os.getenv("STAGING_SOCKET_URI", None)
PROD_SOCKET_PATH = os.getenv("PROD_SOCKET_PATH", None)
STAGING_SOCKET_PATH = os.getenv("STAGING_SOCKET_PATH", None)
