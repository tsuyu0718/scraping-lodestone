import os
from dotenv import load_dotenv

load_dotenv('/.env')
PROJECT_ID = os.getenv('PROJECT_ID')
COLLECTION_NAME = os.getenv('COLLECTION_NAME')