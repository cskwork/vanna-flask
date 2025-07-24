import os
from vanna.openai import OpenAI
from vanna.bedrock import Bedrock
from vanna.ollama import Ollama
from vanna.chromadb import ChromaDB_VectorStore
from vanna.google import Google

# LLM Configuration
def get_llm():
    llm_choice = os.environ.get('LLM', 'ollama').lower()

    if llm_choice == 'openai':
        return OpenAI(config={'api_key': os.environ.get('OPENAI_API_KEY'), 'model': os.environ.get('OPENAI_MODEL', 'gpt-4')})
    elif llm_choice == 'bedrock':
        return Bedrock(config={'model': os.environ.get('BEDROCK_MODEL', 'anthropic.claude-v2')})
    elif llm_choice == 'ollama':
        return Ollama(config={'model': os.environ.get('OLLAMA_MODEL', 'phi3')})
    elif llm_choice == 'google':
        return Google(config={'api_key': os.environ.get('GOOGLE_API_KEY'), 'model': os.environ.get('GOOGLE_MODEL', 'gemini-pro')})
    else:
        raise ValueError(f"Unsupported LLM: {llm_choice}")

# Vector Store Configuration
def get_vector_store():
    vector_store_choice = os.environ.get('VECTOR_STORE', 'chromadb').lower()

    if vector_store_choice == 'chromadb':
        return ChromaDB_VectorStore(config={'path': os.environ.get('CHROMA_PATH', './chroma')})
    # Add other vector stores here as needed
    else:
        raise ValueError(f"Unsupported vector store: {vector_store_choice}")

# Vanna Class
class MyVanna:
    def __new__(cls, config=None):
        llm = get_llm()
        vector_store = get_vector_store()

        # This is a bit of a hack to dynamically create the Vanna class
        # with the correct base classes.
        class_name = f"Vanna_{llm.__class__.__name__}_{vector_store.__class__.__name__}"
        vanna_class = type(class_name, (vector_store.__class__, llm.__class__), {})

        return vanna_class(config={'llm': llm, 'vector_store': vector_store})

# Database Connection
def get_db_connection_params():
    db_choice = os.environ.get('DATABASE', 'sqlite').lower()

    if db_choice == 'sqlite':
        return {'db_type': 'sqlite', 'path': os.environ.get('SQLITE_PATH', 'my-database.sqlite')}
    elif db_choice == 'mysql':
        return {
            'db_type': 'mysql',
            'host': os.environ.get('MYSQL_HOST'),
            'user': os.environ.get('MYSQL_USER'),
            'password': os.environ.get('MYSQL_PASSWORD'),
            'database': os.environ.get('MYSQL_DATABASE'),
        }
    elif db_choice == 'postgresql':
        return {
            'db_type': 'postgresql',
            'host': os.environ.get('POSTGRES_HOST'),
            'user': os.environ.get('POSTGRES_USER'),
            'password': os.environ.get('POSTGRES_PASSWORD'),
            'database': os.environ.get('POSTGRES_DB'),
        }
    # Add other databases here as needed
    else:
        raise ValueError(f"Unsupported database: {db_choice}")