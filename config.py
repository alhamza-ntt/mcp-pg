from dotenv import load_dotenv
import os
import logging

load_dotenv()


COGNITIVE_SEARCH_CONFIG = {
    'api_key': os.environ['COGNITIVE_SEARCH_API_KEY'],
    'endpoint': os.environ['COGNITIVE_SEARCH_ENDPOINT'],
    'index_name': os.environ['COGNITIVE_SEARCH_INDEX_NAME']
}

ADA_CONFIG = {
    'api_key': os.environ['OPENAI_API_KEY'],
    'api_base': os.environ['OPENAI_API_BASE'],
    'api_version': os.environ['ADA_API_VERSION'],
    'model': os.environ['ADA_MODEL'],
    'deployment_name': os.environ['ADA_DEPLOYMENT_NAME']
}
