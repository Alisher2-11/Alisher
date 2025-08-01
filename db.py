import sqlite3

def init_db(db_name):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT UNIQUE,
            location TEXT,
            info TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_client(db_name, name, phone, location, info):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('INSERT INTO clients (name, phone, location, info) VALUES (?, ?, ?, ?)', (name, phone, location, info))
    conn.commit()
    conn.close()

def get_client_by_phone(db_name, phone):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('SELECT * FROM clients WHERE phone = ?', (phone,))
    result = c.fetchone()
    conn.close()
    return result

def update_client_field(db_name, phone, field, new_value):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    query = f'UPDATE clients SET {field} = ? WHERE phone = ?'
    c.execute(query, (new_value, phone))
    conn.commit()
    conn.close()

def delete_client(db_name, phone):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('DELETE FROM clients WHERE phone = ?', (phone,))
    conn.commit()
    conn.close()

def get_all_clients(db_name):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('SELECT * FROM clients')
    result = c.fetchall()
    conn.close()
    return result
