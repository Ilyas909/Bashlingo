import json
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_nested_list(lst, num):
    for sublist in lst:
        for pair in sublist:
            if pair[1] == num:
                return sublist
    return None


try:
    with open("copy_class_lesson.json", "r") as file:
        inf = json.load(file)
        source = inf["source"]
        target = inf["target"]

    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    teacher1 = cursor.execute('SELECT id FROM teacher WHERE username = ?;', (source,)).fetchone()
    teacher1 = teacher1[0]
    if teacher1:
        class_list = cursor.execute('SELECT id, title FROM class_list WHERE teacher_id = ?;', (teacher1,)).fetchall()
        lesson_list = []
        lesson_word_list = []
        lesson_sentences_list = []
        lesson_text_list = []
        lesson_poem_list = []
        for class_id in class_list:
            lesson_list.append(cursor.execute('SELECT * FROM lessons_list WHERE class_id = ?;', (class_id[0],)).fetchall())
            if lesson_list[-1]:
                for i in range(len(lesson_list[-1])):
                    lesson_word_list.append(cursor.execute('SELECT * FROM lesson_word WHERE lesson_id = ?;', (lesson_list[-1][i][0],)).fetchall())
                    lesson_sentences_list.append(cursor.execute('SELECT * FROM lesson_sentences WHERE lesson_id = ?;', (lesson_list[-1][i][0],)).fetchall())
                    lesson_text_list.append(cursor.execute('SELECT * FROM lesson_text WHERE lesson_id = ?;', (lesson_list[-1][i][0],)).fetchall())
                    lesson_poem_list.append(cursor.execute('SELECT * FROM lesson_poem WHERE lesson_id = ?;', (lesson_list[-1][i][0],)).fetchall())
            else:
                lesson_list.pop()

        for username in target:
            teacher2 = cursor.execute('SELECT id FROM teacher WHERE username = ?;', (username,)).fetchone()
            teacher2 = teacher2[0]
            if teacher2:
                for class_id in class_list:
                    cursor.execute('INSERT INTO class_list (title, teacher_id) VALUES (?, ?);',
                                   (class_id[1], teacher2))
                    new_class_id = cursor.lastrowid
                    conn.commit()
                    lessons = find_nested_list(lesson_list, class_id[0])
                    if lessons:
                        for lesson in lessons:
                            cursor.execute(
                                'INSERT INTO lessons_list (class_id, title, matching_game, contents_offer, say_the_word, poem, reading, date_lesson, available) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);',
                                (new_class_id, lesson[2], lesson[3], lesson[4], lesson[5],
                                 lesson[6], lesson[7], lesson[8], lesson[9]))
                            new_lesson_id = cursor.lastrowid
                            conn.commit()

                            words = find_nested_list(lesson_word_list, lesson[0])
                            if words:
                                for word in words:
                                    cursor.execute('INSERT INTO lesson_word (lesson_id, word) VALUES (?, ?);',
                                                   (new_lesson_id, word[2].upper()))
                                conn.commit()

                            sentences = find_nested_list(lesson_sentences_list, lesson[0])
                            if sentences:
                                for word in sentences:
                                    cursor.execute(
                                        'INSERT INTO lesson_sentences (lesson_id, sentences) VALUES (?, ?);',
                                        (new_lesson_id, word[2].strip()))
                                conn.commit()

                            texts = find_nested_list(lesson_text_list, lesson[0])
                            if texts:
                                for line in texts:
                                    cursor.execute(
                                        'INSERT INTO lesson_text (lesson_id, line, startTime, endTime, audioURL) VALUES (?, ?, ?, ?, ?);',
                                        (new_lesson_id, line[2], line[3], line[4], line[5]))
                                conn.commit()

                            poems = find_nested_list(lesson_poem_list, lesson[0])
                            if poems:
                                for poem in poems:
                                    cursor.execute(
                                        'INSERT INTO lesson_poem (lesson_id, double_line, audioURL) VALUES (?, ?, ?);',
                                        (new_lesson_id, poem[2], poem[3]))
                                conn.commit()
    cursor.close()
    conn.close()

except (FileNotFoundError, json.decoder.JSONDecodeError):
    logger.error(f"Ошибка: файл copy_class_lesson.json не существует")
