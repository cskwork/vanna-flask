import os
from vanna.openai import OpenAI
from vanna.bedrock import Bedrock
from vanna.ollama import Ollama
from vanna.chromadb import ChromaDB_VectorStore

def get_llm():
    llm_choice = os.environ.get('LLM', 'ollama').lower()

    if llm_choice == 'openai':
        return OpenAI(config={'api_key': os.environ.get('OPENAI_API_KEY'), 'model': os.environ.get('OPENAI_MODEL', 'gpt-4')})
    elif llm_choice == 'bedrock':
        return Bedrock(config={'model': os.environ.get('BEDROCK_MODEL', 'anthropic.claude-v2')})
    elif llm_choice == 'ollama':
        return Ollama(config={'model': os.environ.get('OLLAMA_MODEL', 'phi3')})
    else:
        raise ValueError(f"Unsupported LLM: {llm_choice}")

def get_vector_store():
    return ChromaDB_VectorStore(config={'path': os.environ.get('CHROMA_PATH', './chroma')})

class MyVanna(ChromaDB_VectorStore, object):
    def __init__(self, config=None):
        self.llm = get_llm()
        self.vector_store = get_vector_store()

        # The following is a bit of a hack to make sure that the LLM and vector store are initialized correctly
        if isinstance(self.llm, OpenAI):
            super(MyVanna, self).__init__(config={'llm': self.llm, 'vector_store': self.vector_store}
        elif isinstance(self.llm, Bedrock):
            super(MyVanna, self).__init__(config={'llm': self.llm, 'vector_store': self.vector_store}
        elif isinstance(self.llm, Ollama):
            super(MyVanna, self).__init__(config={'llm': self.llm, 'vector_store': self.vector_store}

def get_db_connection():
    db_choice = os.environ.get('DATABASE', 'sqlite').lower()

    if db_choice == 'sqlite':
        return {'db_type': 'sqlite', 'path': 'my-database.sqlite'}
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
    else:
        raise ValueError(f"Unsupported database: {db_choice}")
