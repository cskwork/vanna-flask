from dotenv import load_dotenv
load_dotenv()

from vanna.ollama import Ollama
from vanna.chromadb import ChromaDB_VectorStore
import os

class MyVanna(ChromaDB_VectorStore, Ollama):
    def __init__(self, config=None):
        self.chroma_path = os.environ.get('CHROMA_PATH', './chroma')
        self.ollama_model = os.environ.get('OLLAMA_MODEL', 'phi3')

        ChromaDB_VectorStore.__init__(self, config={'path': self.chroma_path})
        Ollama.__init__(self, config={'model': self.ollama_model})

vn = MyVanna()
vn.connect_to_sqlite('my-database.sqlite')

print("Training Vanna...")
df_ddl = vn.run_sql("SELECT type, sql FROM sqlite_master WHERE sql is not null")
for ddl in df_ddl['sql'].to_list():
  vn.train(ddl=ddl)
print("Training complete.")
