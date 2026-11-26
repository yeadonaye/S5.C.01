import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DB_URL")


# Dépendance FastAPI : ouvre une connexion par requête et la ferme à la fin
def get_conn():
    conn = psycopg2.connect(DB_URL)
    try:
        yield conn
    finally:
        conn.close()