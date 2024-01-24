import sqlite3
import random
from datetime import datetime

from starlette.responses import JSONResponse

from api import Login, UserID, NewClass, ClassID, NewName, NewNameStudent, EntityId, GetWords, Entityt, User


def user_exists_by_credentials(log: Login):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    role = 'teacher'
    request = cursor.execute('SELECT * FROM teacher WHERE username = ? AND password = ?',
                             (log.username, log.password)).fetchone()
    if not request:
        request = cursor.execute('SELECT * FROM student WHERE username = ? AND password = ?',
                                 (log.username, log.password)).fetchone()
        role = 'student'
    # Фиксация изменений и закрытие соединения
    cursor.close()
    conn.close()
    return request, role


def get_user_by_id(userID: UserID, role):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    if role == 'teacher':
        request = cursor.execute('SELECT * FROM teacher WHERE id = ?;', (userID.id,)).fetchone()
    elif role == 'student':
        request = cursor.execute('SELECT * FROM student WHERE id = ?;', (userID.id,)).fetchone()
    else:
        request = None
    cursor.close()
    conn.close()
    return request


def get_clssList_by_teacherID(teacherID):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    request = cursor.execute('SELECT id, title FROM class_list WHERE teacher_id = ?;', (teacherID,)).fetchall()

    cursor.close()
    conn.close()

    if not request:
        return []
    result = [{"id": row[0], "title": row[1]} for row in request]
    return result


def add_new_classdb(new_class: NewClass, teacherID):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO class_list (title, teacher_id) VALUES (?, ?);', (new_class.title, teacherID))
        conn.commit()
        added_class_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return added_class_id
    except Exception as e:
        # Если произошла ошибка, откатываем изменения
        print(f"Ошибка: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return None


def transliterate_bashkir_name(name):
    cyrillic_to_latin_mapping = {
        'а': 'a', 'ә': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'ғ': 'g',
        'д': 'd', 'е': 'e', 'ё': 'e', 'ж': 'zh', 'з': 'z', 'и': 'i',
        'й': 'y', 'к': 'k', 'ҡ': 'q', 'л': 'l', 'м': 'm', 'н': 'n',
        'ң': 'ng', 'о': 'o', 'ө': 'o', 'п': 'p', 'р': 'r', 'с': 's',
        'т': 't', 'у': 'u', 'ү': 'u', 'ф': 'f', 'х': 'kh', 'һ': 'h',
        'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y',
        'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya', 'ҙ': 'z', 'ҫ': ''
    }

    name = name.lower()
    result = ''

    for char in name:
        if char in cyrillic_to_latin_mapping:
            result += cyrillic_to_latin_mapping[char]
        elif char.isalpha() or char.isdigit() or char.isspace():
            result += char
        else:
            result += '_'

    return result.capitalize().replace(' ', '_')


def add_new_studentdb(new_class: NewClass, class_id):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    try:
        for i in range(len(new_class.studentsList)):
            username = transliterate_bashkir_name(new_class.studentsList[i])
            res = 1
            k = 0
            login = username
            while res != None:
                login = username + str(k)
                k += 1
                res = cursor.execute('SELECT id FROM student WHERE username = ?;', (login,)).fetchone()
            username = login
            password = ''.join(random.choice('0123456789') for i in range(6))

            cursor.execute('INSERT INTO student (name, class_id, username, password) VALUES (?, ?, ?, ?);',
                           (new_class.studentsList[i], class_id, username, password))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        # Если произошла ошибка, откатываем изменения
        print(f"Ошибка: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False


def get_class_info_by_id(class_id: ClassID):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    class_info = cursor.execute('SELECT id, title FROM class_list WHERE id = ?;', (class_id.id,)).fetchone()
    if class_info:
        class_id, class_title = class_info
        students_list = cursor.execute('SELECT id, class_id, name, username, password FROM student WHERE class_id = ?;',
                                       (class_id,)).fetchall()
        cursor.close()
        conn.close()

        class_data = {
            "id": class_id,
            "title": class_title,
            "studentsList": [{"id": student[0], "classId": student[1], "name": student[2], "username": student[3],
                              "password": student[4]} for student in students_list]
        }

        return {"class": class_data}
    return {"class": None}


def update_class_namedb(class_id: int, new_name: NewName):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()

    try:
        cursor.execute('UPDATE class_list SET title = ? WHERE id = ?;', (new_name.newName, class_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Ошибка при обновлении названия класса: {e}")
        conn.rollback()
        conn.close()
        return False


def update_student_namedb(new_name: NewNameStudent):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE student SET name = ? WHERE id = ?;', (new_name.newName, new_name.studentId))
    conn.commit()
    updated_student = cursor.execute('SELECT * FROM student WHERE id = ?;', (new_name.studentId,)).fetchone()
    cursor.close()
    conn.close()
    return {
        "id": updated_student[0],
        "name": updated_student[1],
        "classId": updated_student[2],
        "username": updated_student[4],
        "password": updated_student[5],
    }


def delete_student(student_id: int):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM student WHERE id = ?;', (student_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Ошибка при обновлении названия класса: {e}")
        conn.rollback()
        conn.close()
        return False


def get_class_lessons_by_id(class_id: EntityId):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    lesson_list = cursor.execute('SELECT * FROM lessons_list WHERE class_id = ?;', (class_id.id,)).fetchall()
    cursor.close()
    conn.close()
    if lesson_list:
        return {"lessons": [
            {"id": lesson[0], "title": lesson[2], "link": 'https://eng.aiteacher.ru/lesson/' + str(lesson[0]),
             "date": lesson[8], "available": lesson[9]} for lesson in lesson_list]}
    else:
        return {"lessons": []}


def text_to_audio(line: str):
    name = line.split(' ')[0]
    endTime = random.randint(2,10)
    return f"{name}.mp3", endTime


def add_lesson(new_lesson: GetWords):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    try:
        date = "2023-04-19T15:00:00Z"
        correspondence, sentence, speaking = 0, 0, 0
        for i in range(len(new_lesson.enabledTasks)):
            print(new_lesson.enabledTasks[i]['type'])
            if new_lesson.enabledTasks[i]['type'] == 'correspondence':
                correspondence = new_lesson.enabledTasks[i]['maxScore']
            elif new_lesson.enabledTasks[i]["type"] == 'sentence':
                sentence = new_lesson.enabledTasks[i]['maxScore']
            elif new_lesson.enabledTasks[i]["type"] == 'speaking':
                speaking = new_lesson.enabledTasks[i]['maxScore']

        cursor.execute(
            'INSERT INTO lessons_list (class_id, title, matching_game, contents_offer, say_the_word, poem, reading, date_lesson, available) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);',
            (new_lesson.classId, new_lesson.theme, correspondence, sentence, speaking,
             True if new_lesson.poem else False, True if new_lesson.reading else False, new_lesson.date, False))
        new_lesson_id = cursor.lastrowid
        conn.commit()

        if len(new_lesson.words) != 0:
            words = new_lesson.words.split(', ')
            for word in words:
                cursor.execute('INSERT INTO lesson_word (lesson_id, word) VALUES (?, ?);', (new_lesson_id, word))
                cursor.execute('INSERT OR IGNORE INTO words_data (word, status) VALUES (?, ?);', (word.lower(), 0))
            conn.commit()


        if len(new_lesson.sentences) != 0:
            sentences = new_lesson.sentences.split('.')
            for word in sentences:
                cursor.execute(
                    'INSERT INTO lesson_sentences (lesson_id, sentences) VALUES (?, ?);', (new_lesson_id, word))
            conn.commit()

        if new_lesson.poem:
            poem = new_lesson.poem.split('\n')
            for i in range(0, len(poem), 2):
                audioURL = poem[i] + '.mp3'
                double_line = poem[i] + '\n' + poem[i+1]
                cursor.execute(
                    'INSERT INTO lesson_poem (lesson_id, double_line, audioURL) VALUES (?, ?, ?);',
                    (new_lesson_id, double_line, audioURL))
            conn.commit()

        if new_lesson.reading:
            reading = new_lesson.reading.split('.')
            time = 0
            for line in reading:
                audioURL, lenTime = text_to_audio(line)
                startTime = time
                endTime = time + lenTime
                time += lenTime + 0.1
                cursor.execute(
                    'INSERT INTO lesson_text (lesson_id, line, startTime, endTime, audioURL) VALUES (?, ?, ?, ?, ?);',
                    (new_lesson_id, line, startTime, endTime, audioURL))
            conn.commit()

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        # Если произошла ошибка, откатываем изменения
        print(f"Ошибка: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False


def get_lessons_by_studentId(studentId):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    classId = cursor.execute('SELECT class_id FROM student WHERE id = ?;', (studentId,)).fetchone()
    if classId:
        classId = int(classId[0])
    else:
        return JSONResponse(status_code=200, content={"message": "Ошибка"})
    lesson_list = cursor.execute('SELECT * FROM lessons_list WHERE class_id = ?;', (classId,)).fetchall()
    cursor.close()
    conn.close()
    if lesson_list:
        return [{"id": lesson[0], "title": lesson[2]} for lesson in lesson_list]
    else:
        return []


def get_lesson_menu_by_lessonId(lessonId: int):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    lesson_menu = cursor.execute('SELECT * FROM lessons_list WHERE id = ?;', (lessonId,)).fetchone()
    cursor.close()
    conn.close()
    if lesson_menu:
        words_to_add = [
            "Nouns" if lesson_menu[3] > 0 else "",
            "Pronouns" if lesson_menu[4] > 0 else "",
            "Verbs" if lesson_menu[5] > 0 else ""
        ]
        # Отфильтруем только непустые значения
        words_to_add = list(filter(lambda word: word != "", words_to_add))
        return {'id': lesson_menu[0], 'title': lesson_menu[2], "tasks": words_to_add}
    else:
        return {}


def get_lesson_by_id(lessonId: int):
    try:
        conn = sqlite3.connect('text.db')
        cursor = conn.cursor()
        title, class_id = cursor.execute('SELECT title, class_id FROM lessons_list WHERE id = ?;', (lessonId,)).fetchone()
        words = cursor.execute('SELECT word FROM lesson_word WHERE lesson_id = ?;', (lessonId,)).fetchall()
        sentences = cursor.execute('SELECT sentences FROM lesson_sentences WHERE lesson_id = ?;', (lessonId,)).fetchall()
        cursor.close()
        conn.close()

        flat_words_list = [word[0] for word in words]
        words = ', '.join(flat_words_list)

        flat_words_list = [word[0] for word in sentences]
        sentences = '. '.join(flat_words_list)

        return {
                  "lesson": {
                    "theme": title,
                    "words": words,
                    "sentences": sentences
                  },
                  "classId": class_id
                }
    except sqlite3:
        return {}


def lesson_availability(availability: Entityt):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE lessons_list SET available = ? WHERE id = ?;', (availability.available, availability.lessonId))
    conn.commit()
    lesson = cursor.execute('SELECT * FROM lessons_list WHERE id = ?;', (availability.lessonId,)).fetchone()
    cursor.close()
    conn.close()
    return {"id": lesson[0], "title": lesson[2], "link": 'https://eng.aiteacher.ru/lesson/' + str(lesson[0]),
             "date": lesson[8], "available": lesson[9]}


def delete_lesson_by_id(lesson_id: int, classId: int):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()

    try:
        claass = cursor.execute('SELECT class_id FROM lessons_list WHERE id = ?;', (lesson_id,)).fetchone()
        if classId == claass[0]:
            cursor.execute('DELETE FROM lessons_list WHERE id = ?;', (lesson_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return JSONResponse(status_code=200, content={"message": "Урок удален"})
        else:
            return JSONResponse(status_code=400, content={"message": "Неверный classId"})
    except Exception as e:
        print(f"Ошибка при обновлении названия класса: {e}")
        conn.rollback()
        conn.close()
        return JSONResponse(status_code=500, content={"message": "Не удалось удалить урок"})


def fetch_lesson_results(lessonId: EntityId):
    try:
        lessonId = lessonId.id
        conn = sqlite3.connect('text.db')
        cursor = conn.cursor()
        lessonTitle, maxCorrespondenceResult, maxSentenceResult, maxSpeakingResult = cursor.execute('SELECT title, matching_game, contents_offer, say_the_word FROM lessons_list WHERE id = ?;', (lessonId,)).fetchone()

        results = cursor.execute('''
            SELECT student.id, student.name, solving_result.correspondenceResult, solving_result.sentenceResult, solving_result.speakingResult
            FROM student
            JOIN solving_result ON student.id = solving_result.student_id
            WHERE solving_result.lesson_id = ?;
        ''', (lessonId,)).fetchall()

        cursor.close()
        conn.close()

        for row in results:
            student_id, student_name, correspondence_result, sentence_result, speaking_result = row
            print(
                f"Student ID: {student_id}, Name: {student_name}, Correspondence Result: {correspondence_result}, Sentence Result: {sentence_result}, Speaking Result: {speaking_result}")

        return {
                    "lessonResults": {
                        "lessonTitle": lessonTitle,
                        "studentsResults": [
                                {
                                "id": row[0],
                                "name": row[1],
                                "correspondenceResult": row[2],
                                "sentenceResult": row[3],
                                "speakingResult": row[4]
                                } for row in results
                            ],
                        "maxCorrespondenceResult": maxCorrespondenceResult,
                        "maxSentenceResult": maxSentenceResult,
                        "maxSpeakingResult": maxSpeakingResult
                        }
                    }
    except sqlite3:
        return {}


def username_update(userId: int, username: User):
    try:
        conn = sqlite3.connect('text.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE student SET username = ? WHERE id = ?;',
                       (username, userId))
        conn.commit()
        cursor.close()
        conn.close()
        return JSONResponse(status_code=200, content={"message": "Успешно"})
    except sqlite3.Error as e:
        return JSONResponse(status_code=500, content={"message": e})


def get_username(userId):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    request = cursor.execute('SELECT username FROM student WHERE id = ?;', (userId,)).fetchone()
    cursor.close()
    conn.close()
    return request


def save_avatar(userId: int, avatar: str):
    try:
        conn = sqlite3.connect('text.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE student SET avatar = ? WHERE id = ?;', (avatar, userId))
        conn.commit()
        cursor.close()
        conn.close()
        return {"url": avatar}
    except sqlite3.Error as e:
        return JSONResponse(status_code=500, content={"message":'не удалось сохранить файл'})


def check_student(userId: int, lessonId: int):
    try:
        conn = sqlite3.connect('text.db')
        cursor = conn.cursor()
        user_classId = cursor.execute('SELECT class_id FROM student WHERE id = ?;', (userId,)).fetchone()
        lesson_classId = cursor.execute('SELECT class_id FROM lessons_list WHERE id = ?;', (lessonId,)).fetchone()
        if int(user_classId[0]) == lesson_classId[0]:
            cursor.close()
            conn.close()
            return True
        else:
            cursor.close()
            conn.close()
            return False
    except sqlite3.Error as e:
        print(e)
        return False


def image_words(lessonId: int):
    try:
        conn = sqlite3.connect('text.db')
        cursor = conn.cursor()
        result = cursor.execute('SELECT lw.id, wd.word, wd.image FROM words_data wd JOIN lesson_word lw ON wd.word = lw.word WHERE lw.lesson_id = ? AND wd.status = 1;', (lessonId,)).fetchall()
        cursor.close()
        conn.close()
        if result:
            return [{"id": res[0], "word": res[1], "image": res[2]} for res in result]
        return []
    except sqlite3.Error as e:
        return JSONResponse(status_code=500, content={"message":'поиск не удался'})


def get_poem_audio(lessonId: int):
    try:
        conn = sqlite3.connect('text.db')
        cursor = conn.cursor()
        result = cursor.execute('SELECT double_line, audioURL FROM lesson_poem WHERE lesson_id = ?;', (lessonId,)).fetchall()
        cursor.close()
        conn.close()
        big_audio = ''.join(audio[1] for audio in result)

        if result:
            return [
                      {
                        "audio": big_audio,
                        "parts": [
                          {
                            "smallAudio": line[1],
                            "rowOne": line[0].split('\n')[0],
                            "rowTwo": line[0].split('\n')[1]
                          } for line in result
                        ]
                      }
                    ]
        return []
    except sqlite3.Error as e:
        return JSONResponse(status_code=500, content={"message":'поиск не удался'})


def get_text_audio(lessonId: int):
    try:
        conn = sqlite3.connect('text.db')
        cursor = conn.cursor()
        result = cursor.execute('SELECT line, startTime, endTime, audioURL FROM lesson_text WHERE lesson_id = ?;', (lessonId,)).fetchall()
        cursor.close()
        conn.close()
        title = result[0][0]
        big_audio = ''.join(audio[3] for audio in result)

        if result:
            return {
                      "title": title,
                      "audio": big_audio,
                      "paragraphs": [
                        {
                          "sentences": [
                            {
                              "text": line[0],
                              "start": line[1],
                              "end": line[2]
                            } for line in result
                          ]
                        }
                      ]
                    }
        return []
    except sqlite3.Error as e:
        return JSONResponse(status_code=500, content={"message": 'поиск не удался'})




def edit_lesson_lessonId(new_lesson: GetWords):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    try:
        correspondence, sentence, speaking = 0, 0, 0
        for i in range(len(new_lesson.enabledTasks)):
            print(new_lesson.enabledTasks[i]['type'])
            if new_lesson.enabledTasks[i]['type'] == 'correspondence':
                correspondence = new_lesson.enabledTasks[i]['maxScore']
            elif new_lesson.enabledTasks[i]["type"] == 'sentence':
                sentence = new_lesson.enabledTasks[i]['maxScore']
            elif new_lesson.enabledTasks[i]["type"] == 'speaking':
                speaking = new_lesson.enabledTasks[i]['maxScore']



        cursor.execute(
        'UPDATE lessons_list SET class_id = ?, title = ?, matching_game = ?, contents_offer = ?, say_the_word = ?, poem = ?, reading = ?, date_lesson = ?, available = ? WHERE id = ?;', (new_lesson.classId, new_lesson.theme, correspondence, sentence, speaking,
             True if new_lesson.poem else False, True if new_lesson.reading else False, new_lesson.date, False, new_lesson.lessonId))

        new_lesson_id = cursor.lastrowid
        conn.commit()

        cursor.execute('DELETE FROM lesson_word WHERE lesson_id = ?;', (new_lesson.lessonId,))
        if len(new_lesson.words) != 0:
            words = new_lesson.words.split(', ')
            for word in words:
                cursor.execute('INSERT INTO lesson_word (lesson_id, word) VALUES (?, ?);', (new_lesson.lessonId, word))
                cursor.execute('INSERT OR IGNORE INTO words_data (word, status) VALUES (?, ?);', (word.lower(), 0))
            conn.commit()


        cursor.execute('DELETE FROM lesson_sentences WHERE lesson_id = ?;', (new_lesson.lessonId,))
        if len(new_lesson.sentences) != 0:
            sentences = new_lesson.sentences.split('.')
            for word in sentences:
                cursor.execute(
                    'INSERT INTO lesson_sentences (lesson_id, sentences) VALUES (?, ?);', (new_lesson.lessonId, word))
            conn.commit()

        cursor.execute('DELETE FROM lesson_poem WHERE lesson_id = ?;', (new_lesson.lessonId,))
        if new_lesson.poem:
            poem = new_lesson.poem.split('\n')
            for i in range(0, len(poem), 2):
                audioURL = poem[i] + '.mp3'
                double_line = poem[i] + '\n' + poem[i+1]
                cursor.execute(
                    'INSERT INTO lesson_poem (lesson_id, double_line, audioURL) VALUES (?, ?, ?);',
                    (new_lesson_id, double_line, audioURL))
            conn.commit()

        cursor.execute('DELETE FROM lesson_text WHERE lesson_id = ?;', (new_lesson.lessonId,))
        if new_lesson.reading:
            reading = new_lesson.reading.split('.')
            time = 0
            for line in reading:
                audioURL, lenTime = text_to_audio(line)
                startTime = time
                endTime = time + lenTime
                time += lenTime + 0.1
                cursor.execute(
                    'INSERT INTO lesson_text (lesson_id, line, startTime, endTime, audioURL) VALUES (?, ?, ?, ?, ?);',
                    (new_lesson_id, line, startTime, endTime, audioURL))
            conn.commit()

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        # Если произошла ошибка, откатываем изменения
        print(f"Ошибка: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False
