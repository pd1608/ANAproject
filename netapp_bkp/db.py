import sqlite3

DB_NAME = "devices.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS devices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_name TEXT NOT NULL,
                        vendor TEXT NOT NULL,
                        wan_ip TEXT NOT NULL,
                        routing_protocol TEXT NOT NULL,
                        j2_template TEXT NOT NULL
                    )''')
    conn.commit()
    conn.close()

