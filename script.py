import sqlite3

conn = sqlite3.connect('text.db')
cursor = conn.cursor()
cursor.execute('INSERT INTO teacher (username, password) VALUES (?, ?);',
            ("ilasn909@gmail.com", "22"))
conn.commit()
cursor.close()
conn.close()