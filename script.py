import json
import random
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
try:
    with open("inf_teacher.json", "r") as file:
        inf_teacher = json.load(file)
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    for inf in inf_teacher:
        password = ''.join(random.choice('0123456789') for i in range(6))
        cursor.execute('INSERT INTO teacher (name, username, password) VALUES (?, ?, ?);',
                       (inf["username"], inf["username"], password))
    conn.commit()
    cursor.close()
    conn.close()
except (FileNotFoundError, json.decoder.JSONDecodeError):
    logger.error(f"Ошибка: файл inf_teacher.json не существует")


