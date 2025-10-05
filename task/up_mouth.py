import sqlite3

def create_connection(db_path="./database.sqlite"):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        print("Connection established")
    except sqlite3.Error as e:
        print(e)
    return conn

def connect_db():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mouth_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mois INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            
        )
    ''')
    conn.commit()
    return conn

def close_connection(conn):
    if conn:
        conn.close()
        print("Connection closed")


def update_mouth_task(conn, mois):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO mouth_tasks (mois) VALUES (?)", (mois,))
    conn.commit()

def get_mouth_tasks(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mouth_tasks")
    rows = cursor.fetchall()
    return rows

