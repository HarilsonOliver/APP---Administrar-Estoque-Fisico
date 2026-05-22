import os
import oracledb

DB_CONFIG = {"user": "frijel", "password": "Afd8505", "dsn": "10.1.1.200:1521/WINT"}
CLIENT_PATH = r"P:\Oracle_Client\instantclient_23_8"

def init_oracle():
    if os.path.exists(CLIENT_PATH):
        try:
            oracledb.init_oracle_client(lib_dir=CLIENT_PATH)
        except: pass