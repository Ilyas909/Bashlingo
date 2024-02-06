import math
from datetime import datetime, timezone
import json
import os
import sqlite3
import random
from json import JSONDecodeError
from collections import defaultdict
from fastapi import FastAPI
from pydub import AudioSegment
from razdel import sentenize
from starlette.staticfiles import StaticFiles
from nail_tts import main
from starlette.responses import JSONResponse
from api import Login, UserID, NewClass, NewName, NewNameStudent, EntityId, GetWords, Entityt, User, ResultGame
import logging


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    with open("config.json", "r") as file:
        inf = json.load(file)
        url_server = inf["url_server"]
        user_is_secure = inf["user_is_secure"]
except (FileNotFoundError, json.decoder.JSONDecodeError):
    raise JSONDecodeError("config.json not found")


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
        logger.error(f"Ошибка: {e}")
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
        logger.error(f"Ошибка: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False


def get_class_info_by_id(class_id: EntityId):
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
        logger.error(f"Ошибка: {e}")
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
        logger.error(f"Ошибка: {e}")
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
    endTime = random.randint(2, 10)
    return f"{name}.mp3", endTime


def convert_wav_to_mp3(input_file, url):
    sound = AudioSegment.from_wav(f"{url}/{input_file}")
    output_file = os.path.splitext(input_file)[0] + ".mp3"
    sound.export(f"{url}/{output_file}", format="mp3")
    os.remove(f"{url}/{input_file}")
    return output_file


def add_lesson(new_lesson: GetWords):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    try:
        correspondence, sentence, speaking = 0, 0, 0
        for i in range(len(new_lesson.enabledTasks)):
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
            url = 'static/audio_word'
            if not os.path.exists(f"./{url}"):
                os.makedirs(f"./{url}")
            words = new_lesson.words.split(', ')
            for word in words:
                cursor.execute('INSERT INTO lesson_word (lesson_id, word) VALUES (?, ?);',
                               (new_lesson_id, word.upper()))
                conn.commit()
                cursor.execute('INSERT OR IGNORE INTO words_data (word, status) VALUES (?, ?);', (word.upper(), 0))
                if cursor.rowcount > 0:
                    audio_url = main(word.lower(), url, word.upper())
                    audio_url = convert_wav_to_mp3(audio_url, url)
                    cursor.execute('UPDATE words_data SET audio = ? WHERE word = ?;',
                                   (audio_url, word.upper()))

            conn.commit()

        if len(new_lesson.sentences) != 0:
            sentences = new_lesson.sentences.split('.')
            for word in sentences:
                if contains_letters_or_digits(word):
                    cursor.execute(
                        'INSERT INTO lesson_sentences (lesson_id, sentences) VALUES (?, ?);',
                        (new_lesson_id, word.strip()))
            conn.commit()

        if new_lesson.poem:
            url = 'static/audio_poem'
            if not os.path.exists(f"./{url}"):
                os.makedirs(f"./{url}")
            poem1 = new_lesson.poem.split('\n')
            poem = [item for item in poem1 if item.strip() != ""]
            for i in range(0, len(poem), 2):
                double_line = poem[i] + '\n' + poem[i + 1] if i + 1 < len(poem) else poem[i]
                cursor.execute(
                    'INSERT INTO lesson_poem (lesson_id, double_line) VALUES (?, ?);',
                    (new_lesson_id, double_line))
                lesson_id = cursor.lastrowid
                double_line = double_line.split('\n')
                audio0 = main(double_line[0], url, f"{lesson_id}0v")
                audioURL1 = convert_wav_to_mp3(audio0, url)
                output_file = f"{lesson_id}.mp3"
                if i + 1 < len(poem):
                    audio1 = main(double_line[1], url, f"{lesson_id}1v")
                    audioURL2 = convert_wav_to_mp3(audio1, url)
                    concatenate_audio_with_pause([f'static/audio_poem/{audioURL1}', f'static/audio_poem/{audioURL2}'],
                                             f'static/audio_poem/{output_file}')
                    os.remove(f'static/audio_poem/{audioURL2}')
                else:
                    concatenate_audio_with_pause([f'static/audio_poem/{audioURL1}'],
                                                 f'static/audio_poem/{output_file}')
                os.remove(f'static/audio_poem/{audioURL1}')

                cursor.execute('UPDATE lesson_poem SET audioURL = ? WHERE id = ?;',
                               (output_file, lesson_id))

            conn.commit()

        if new_lesson.reading:
            url = 'static/audio_text'
            if not os.path.exists(f"./{url}"):
                os.makedirs(f"./{url}")
            reading = new_lesson.reading
            substrings_list = list(sentenize(reading))
            reading = [substring.text for substring in substrings_list]
            # reading = re.split(r'(?<=[.!?\n])\s+', reading)
            startTime = 0
            for line in reading:
                if contains_letters_or_digits(line):
                    cursor.execute(
                        'INSERT INTO lesson_text (lesson_id, line) VALUES (?, ?);',
                        (new_lesson_id, line))
                    lesson_id = cursor.lastrowid
                    audioURL = main(line, url, lesson_id)
                    audioURL = convert_wav_to_mp3(audioURL, url)
                    endTime = startTime + get_audio_length(f'{url}/{audioURL}')
                    cursor.execute('UPDATE lesson_text SET startTime = ?, endTime = ?, audioURL = ? WHERE id = ?;',
                                   (startTime, endTime, audioURL, lesson_id))
                    startTime = endTime + 400
                else:
                    continue
            conn.commit()

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        # Если произошла ошибка, откатываем изменения
        logger.error(f"Ошибка: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False


def contains_letters_or_digits(s):
    return any(c.isalnum() for c in s)


def get_audio_length(file_path):
    audio = AudioSegment.from_file(file_path)
    duration_in_seconds = len(audio)
    return duration_in_seconds


def get_lessons_by_studentId(studentId):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    classId = cursor.execute('SELECT class_id FROM student WHERE id = ?;', (studentId,)).fetchone()
    if classId:
        classId = int(classId[0])
    else:
        return JSONResponse(status_code=200, content={"message": "Ошибка"})
    lesson_list = cursor.execute('SELECT * FROM lessons_list WHERE class_id = ? AND available = true;',
                                 (classId,)).fetchall()
    cursor.close()
    conn.close()
    if lesson_list:
        return [{"id": lesson[0], "title": lesson[2]} for lesson in lesson_list]
    else:
        return []


def get_lesson_menu_by_lessonId(lessonId: int, userId: int):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    lesson_menu = cursor.execute('SELECT * FROM lessons_list WHERE id = ?;', (lessonId,)).fetchone()
    if lesson_menu[3] > 0:
        NounsCurrentScore = cursor.execute('''
                    SELECT 
                        COUNT(*) as count_true_results
                    FROM solving_result
                    WHERE results = true AND lesson_id = ? AND student_id = ? AND job_type = ?
                    ''', (lessonId, userId, 'correspondence')).fetchone()
    if lesson_menu[4] > 0:
        PronounsCurrentScore = cursor.execute('''
                    SELECT 
                        COUNT(*) as count_true_results
                    FROM solving_result
                    WHERE results = true AND lesson_id = ? AND student_id = ? AND job_type = ?
                    ''', (lessonId, userId, 'sentence')).fetchone()

    if lesson_menu[5] > 0:
        VerbsCurrentScore = cursor.execute('''
                    SELECT 
                        COUNT(*) as count_true_results
                    FROM solving_result
                    WHERE results = true AND lesson_id = ? AND student_id = ? AND job_type = ?
                    ''', (lessonId, userId, 'speaking')).fetchone()
    cursor.close()
    conn.close()
    if lesson_menu:
        words_to_add = [
            {'name': "Nouns", 'maxScore': lesson_menu[3], 'currentScore': NounsCurrentScore[0]} if lesson_menu[
                                                                                                    3] > 0 else "",
            {'name': "Pronouns", 'maxScore': lesson_menu[4], 'currentScore': PronounsCurrentScore[0]} if lesson_menu[
                                                                                                          4] > 0 else "",
            {'name': "Verbs", 'maxScore': lesson_menu[5], 'currentScore': VerbsCurrentScore[0]} if lesson_menu[
                                                                                                    5] > 0 else "",
            {'name': "Poem"} if lesson_menu[6] else "",
            {'name': "Read"} if lesson_menu[7] else ""
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
        title, class_id, date_lesson, correspondence, sentence, speaking = cursor.execute(
            'SELECT title, class_id, date_lesson, matching_game, contents_offer, say_the_word FROM lessons_list WHERE id = ?;',
            (lessonId,)).fetchone()
        words = cursor.execute('SELECT word FROM lesson_word WHERE lesson_id = ?;', (lessonId,)).fetchall()
        sentences = cursor.execute('SELECT sentences FROM lesson_sentences WHERE lesson_id = ?;',
                                   (lessonId,)).fetchall()
        poem = cursor.execute('SELECT double_line FROM lesson_poem WHERE lesson_id = ?;', (lessonId,)).fetchall()
        reading = cursor.execute('SELECT line FROM lesson_text WHERE lesson_id = ?;', (lessonId,)).fetchall()

        cursor.close()
        conn.close()

        flat_words_list = [word[0] for word in words]
        words = ', '.join(flat_words_list)

        flat_words_list = [word[0] for word in sentences]
        sentences = '. '.join(flat_words_list)

        flat_words_list = [word[0] for word in poem]
        poem = '\n'.join(flat_words_list)

        flat_words_list = [word[0] for word in reading]
        reading = '. '.join(flat_words_list)

        enabledTasks = []
        if correspondence > 0:
            enabledTasks.append({"type": 'correspondence', "maxScore": correspondence})
        if sentence > 0:
            enabledTasks.append({"type": 'sentence', "maxScore": sentence})
        if speaking > 0:
            enabledTasks.append({"type": 'speaking', "maxScore": speaking})

        return {
            "lesson": {
                "theme": title,
                "words": words,
                "sentences": sentences,
                "poem": poem,
                "reading": reading,
                "date": date_lesson,
                "enabledTasks": enabledTasks
            },
            "classId": class_id
        }
    except sqlite3:
        return {}


def lesson_availability(availability: Entityt):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE lessons_list SET available = ? WHERE id = ?;',
                   (availability.available, availability.lessonId))
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
            cursor.execute('PRAGMA foreign_keys = ON;')
            poem_audio = cursor.execute('SELECT audioURL FROM lesson_poem WHERE lesson_id = ?;',
                                        (lesson_id,)).fetchall()
            text_audio = cursor.execute('SELECT audioURL FROM lesson_text WHERE lesson_id = ?;',
                                        (lesson_id,)).fetchall()
            cursor.execute('DELETE FROM lessons_list WHERE id = ?;', (lesson_id,))
            conn.commit()
            cursor.close()
            conn.close()
            for file_url in poem_audio:
                if file_url[0]:
                    os.remove(f"static/audio_poem/{file_url[0]}")

            for file_url in text_audio:
                if file_url[0]:
                    os.remove(f"static/audio_text/{file_url[0]}")

            return JSONResponse(status_code=200, content={"message": "Урок удален"})
        else:
            return JSONResponse(status_code=400, content={"message": "Неверный classId"})
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        conn.rollback()
        conn.close()
        return JSONResponse(status_code=500, content={"message": "Не удалось удалить урок"})


def fetch_lesson_results(lessonId: EntityId):
    try:
        lessonId = lessonId.id
        conn = sqlite3.connect('text.db')
        cursor = conn.cursor()
        lessonTitle, maxCorrespondenceResult, maxSentenceResult, maxSpeakingResult = cursor.execute(
            'SELECT title, matching_game, contents_offer, say_the_word FROM lessons_list WHERE id = ?;',
            (lessonId,)).fetchone()

        results = cursor.execute('''
            SELECT student.id, student.name, job_type, COUNT(*) as count_true_results
            FROM solving_result
            JOIN student ON student.id = solving_result.student_id
            WHERE results = true AND lesson_id = ?
            GROUP BY student_id, job_type;
        ''', (lessonId,)).fetchall()

        cursor.close()
        conn.close()

        student_results = defaultdict(lambda: {'correspondenceResult': 0, 'sentenceResult': 0, 'speakingResult': 0})
        for item in results:
            student_id, name, job_type, result = item
            student_results[student_id]['id'] = student_id
            student_results[student_id]['name'] = name
            student_results[student_id][f'{job_type}Result'] += result

        result_json = list(student_results.values())

        return {
            "lessonResults": {
                "lessonTitle": lessonTitle,
                "studentsResults": result_json,
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
        return JSONResponse(status_code=500, content={"message": 'не удалось сохранить файл'})


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
        logger.error(f"Ошибка: {e}")
        return False


def image_words(lessonId: int, userId: int):
    try:
        conn = sqlite3.connect('text.db')
        cursor = conn.cursor()
        count_task = cursor.execute('SELECT matching_game FROM lessons_list WHERE id = ?;',
                                    (lessonId,)).fetchone()
        result = cursor.execute(
            'SELECT lw.id, wd.word, wd.image, wd.audio FROM words_data wd JOIN lesson_word lw ON wd.word = lw.word WHERE lw.lesson_id = ? AND wd.status = 1;',
            (lessonId,)).fetchall()
        right_word = cursor.execute(
            'SELECT item_id FROM solving_result WHERE lesson_id = ? AND student_id = ? AND job_type = "correspondence" AND results = true;',
            (lessonId, userId,)).fetchall()
        PronounsCurrentScore = cursor.execute('''
                                    SELECT 
                                        COUNT(*) as count_true_results
                                    FROM solving_result
                                    WHERE results = true AND lesson_id = ? AND student_id = ? AND job_type = ?
                                    ''', (lessonId, userId, 'correspondence')).fetchone()
        cursor.close()
        conn.close()

        count_task = count_task[0]
        result_list = [item[0] for item in right_word]
        right_word = result_list
        remainder = count_task - PronounsCurrentScore[0]
        if result and count_task > PronounsCurrentScore[0]:
            if count_task > len(result):
                result *= math.ceil(count_task / len(result))
                result = result[:count_task]
            elif count_task < len(result):
                result = result[:count_task]

            # if right_word:
            for wordId in result:
                if right_word:
                    if list(wordId)[0] in right_word:
                        result.reverse()
                        result.remove(wordId)
                        result.reverse()
                        right_word.pop(0)
                else:
                    break

            result = list(set(result))
            if len(result) > remainder:
                result = result[:remainder]

            return {'tasks': [{"id": res[0], "word": res[1], "image": f"{url_server}/static/image_word/{res[2]}",
                               "audioUrl": f"{url_server}/static/audio_word/{res[3]}"} for res in
                              result], 'currentScore': PronounsCurrentScore[0], 'maxScore': count_task}
        return {'tasks': [], 'currentScore': PronounsCurrentScore[0], 'maxScore': count_task}
    except sqlite3.Error as e:
        return JSONResponse(status_code=404, content={"message": 'поиск не удался'})


def get_sentence(lessonId: int, userId: int):
    try:
        conn = sqlite3.connect('text.db')
        cursor = conn.cursor()
        count_task = cursor.execute('SELECT contents_offer FROM lessons_list WHERE id = ?;',
                                    (lessonId,)).fetchone()
        result = cursor.execute('SELECT id, sentences FROM lesson_sentences WHERE lesson_id = ?;',
                                (lessonId,)).fetchall()
        right_word = cursor.execute(
            'SELECT item_id FROM solving_result WHERE lesson_id = ? AND student_id = ? AND job_type = "sentence" AND results = true;',
            (lessonId, userId,)).fetchall()

        PronounsCurrentScore = cursor.execute('''
                            SELECT 
                                COUNT(*) as count_true_results
                            FROM solving_result
                            WHERE results = true AND lesson_id = ? AND student_id = ? AND job_type = ?
                            ''', (lessonId, userId, 'sentence')).fetchone()
        cursor.close()
        conn.close()

        count_task = count_task[0]
        result_list = [item[0] for item in right_word]
        right_word = result_list
        remainder = count_task - PronounsCurrentScore[0]

        if result and count_task > PronounsCurrentScore[0]:
            if count_task > len(result):
                result *= math.ceil(count_task / len(result))
                result = result[:count_task]
            elif count_task < len(result):
                result = result[:count_task]

            # if right_word:
            for wordId in result:
                if right_word:
                    if list(wordId)[0] in right_word:
                        result.reverse()
                        result.remove(wordId)
                        result.reverse()
                        right_word.pop(0)
                else:
                    break

            result = list(set(result))
            if len(result) > remainder:
                result = result[:remainder]
            return {'tasks': [{"id": res[0], "sentence": res[1]} for res in result], 'currentScore': PronounsCurrentScore[0],
                    'maxScore': count_task}
        return {'tasks': [], 'currentScore': PronounsCurrentScore[0], 'maxScore': count_task}
    except sqlite3.Error as e:
        return JSONResponse(status_code=404, content={"message": 'поиск не удался'})


def get_speaking(lessonId: int, userId: int):
    try:
        conn = sqlite3.connect('text.db')
        cursor = conn.cursor()
        count_task = cursor.execute('SELECT say_the_word FROM lessons_list WHERE id = ?;',
                                    (lessonId,)).fetchone()
        result = cursor.execute('SELECT id, word FROM lesson_word WHERE lesson_id = ?;', (lessonId,)).fetchall()
        right_word = cursor.execute(
            'SELECT item_id FROM solving_result WHERE lesson_id = ? AND student_id = ? AND job_type = "speaking" AND results = true;',
            (lessonId, userId,)).fetchall()
        PronounsCurrentScore = cursor.execute('''
                                    SELECT 
                                        COUNT(*) as count_true_results
                                    FROM solving_result
                                    WHERE results = true AND lesson_id = ? AND student_id = ? AND job_type = ?
                                    ''', (lessonId, userId, 'speaking')).fetchone()
        cursor.close()
        conn.close()

        count_task = count_task[0]
        result_list = [item[0] for item in right_word]
        right_word = result_list
        remainder = count_task - PronounsCurrentScore[0]

        if result and count_task > PronounsCurrentScore[0]:
            if count_task > len(result):
                result *= math.ceil(count_task / len(result))
                result = result[:count_task]
            elif count_task < len(result):
                result = result[:count_task]

            # if right_word:
            for wordId in result:
                if right_word:
                    if list(wordId)[0] in right_word:
                        result.reverse()
                        result.remove(wordId)
                        result.reverse()
                        right_word.pop(0)
                else:
                    break

            result = list(set(result))
            if len(result) > remainder:
                result = result[:remainder]
            return {'tasks': [{"id": res[0], "text": res[1]} for res in result], 'currentScore': PronounsCurrentScore[0],
                    'maxScore': count_task}
        return {'tasks': [], 'currentScore': PronounsCurrentScore[0], 'maxScore': count_task}
    except sqlite3.Error as e:
        return JSONResponse(status_code=404, content={"message": 'поиск не удался'})


def get_poem_audio(lessonId: int):
    try:
        if not os.path.exists(f"./static/audio_big_poem"):
            os.makedirs(f"./static/audio_big_poem")
        conn = sqlite3.connect('text.db')
        cursor = conn.cursor()
        result = cursor.execute('SELECT double_line, audioURL, id FROM lesson_poem WHERE lesson_id = ?;',
                                (lessonId,)).fetchall()
        cursor.close()
        conn.close()

        files = []
        for res in result:
            files.append(f"static/audio_poem/{res[1]}")

        big_audios = []
        for i in range(0, len(files), 2):
            output_file = f'{lessonId}l{i}.mp3'
            if len(files) > i+1:
                concatenate_audio_with_pause([files[i], files[i + 1]], f"static/audio_big_poem/{output_file}")
            else:
                concatenate_audio_with_pause([files[i]], f"static/audio_big_poem/{output_file}")

            big_audios.append(f"{url_server}/static/audio_big_poem/{output_file}")

        if result:
            return [
                {
                    "audio": big_audio,
                    "parts": [
                        {
                            "smallAudio": f"{url_server}/static/audio_poem/{result[k][1]}",
                            "rowOne": result[k][0].split('\n')[0],
                            "rowTwo": result[k][0].split('\n')[1] if len(result[k][0].split('\n')) > 1 else '',
                            "id": result[k][2]
                        } for k in range(i * 2, i * 2 + 2) if len(result) > k
                    ],
                    "id": i+1
                } for i, big_audio in enumerate(big_audios)
            ]

        return []
    except sqlite3.Error as e:
        logger.error(f"Ошибка: {e}")
        return JSONResponse(status_code=500, content={"message": 'поиск не удался'})


def concatenate_audio_with_pause(files, output_file, pause_duration=400):
    pause = AudioSegment.silent(duration=pause_duration)

    # Список для хранения аудиосегментов
    segments = []

    # Загружаем каждый аудиофайл и добавляем его в список
    for file in files:
        segment = AudioSegment.from_file(file)
        segments.append(segment)
        segments.append(pause)  # Добавляем паузу после каждого аудиофайла

    # Убираем последнюю паузу
    segments.pop()

    # Объединяем все аудиосегменты
    result = AudioSegment.empty()
    for segment in segments:
        result += segment

    result.export(output_file, format="mp3")


def get_text_audio(lessonId: int):
    try:
        if not os.path.exists(f"./static/audio_big_text"):
            os.makedirs(f"./static/audio_big_text")
        conn = sqlite3.connect('text.db')
        cursor = conn.cursor()
        result = cursor.execute('SELECT line, startTime, endTime, audioURL, id FROM lesson_text WHERE lesson_id = ?;',
                                (lessonId,)).fetchall()
        cursor.close()
        conn.close()
        files = []
        for res in result:
            files.append(f"static/audio_text/{res[3]}")
        output_file = f'{lessonId}.mp3'
        concatenate_audio_with_pause(files, f"static/audio_big_text/{output_file}")
        title = result[0][0]
        streaming_audio_url = f"{url_server}/big_audio/{lessonId}"
        if result:
            return {
                "title": title,
                "audio": streaming_audio_url,
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
        logger.error(f"Ошибка: {e}")
        return JSONResponse(status_code=500, content={"message": 'поиск не удался'})


def edit_lesson_lessonId(new_lesson: GetWords):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    try:
        correspondence, sentence, speaking = 0, 0, 0
        for i in range(len(new_lesson.enabledTasks)):
            if new_lesson.enabledTasks[i]['type'] == 'correspondence':
                correspondence = new_lesson.enabledTasks[i]['maxScore']
            elif new_lesson.enabledTasks[i]["type"] == 'sentence':
                sentence = new_lesson.enabledTasks[i]['maxScore']
            elif new_lesson.enabledTasks[i]["type"] == 'speaking':
                speaking = new_lesson.enabledTasks[i]['maxScore']

        cursor.execute(
            'UPDATE lessons_list SET class_id = ?, title = ?, matching_game = ?, contents_offer = ?, say_the_word = ?, poem = ?, reading = ?, date_lesson = ? WHERE id = ?;',
            (new_lesson.classId, new_lesson.theme, correspondence, sentence, speaking,
             True if new_lesson.poem else False, True if new_lesson.reading else False, new_lesson.date,
             new_lesson.lessonId))

        new_lesson_id = cursor.lastrowid
        conn.commit()

        cursor.execute('DELETE FROM lesson_word WHERE lesson_id = ?;', (new_lesson.lessonId,))
        if len(new_lesson.words) != 0:
            url = 'static/audio_word'
            words = new_lesson.words.split(', ')
            for word in words:
                cursor.execute('INSERT INTO lesson_word (lesson_id, word) VALUES (?, ?);',
                               (new_lesson.lessonId, word.upper()))
                conn.commit()
                cursor.execute('INSERT OR IGNORE INTO words_data (word, status) VALUES (?, ?);', (word.upper(), 0))
                if cursor.rowcount > 0:
                    audio_url = main(word.lower(), url, word.upper())
                    audio_url = convert_wav_to_mp3(audio_url, url)
                    cursor.execute('UPDATE words_data SET audio = ? WHERE word = ?;',
                                   (audio_url, word.upper()))
            conn.commit()

        cursor.execute('DELETE FROM lesson_sentences WHERE lesson_id = ?;', (new_lesson.lessonId,))
        if len(new_lesson.sentences) != 0:
            sentences = new_lesson.sentences.split('.')
            for word in sentences:
                cursor.execute(
                    'INSERT INTO lesson_sentences (lesson_id, sentences) VALUES (?, ?);',
                    (new_lesson.lessonId, word.strip()))
            conn.commit()

        cursor.execute('DELETE FROM lesson_poem WHERE lesson_id = ?;', (new_lesson.lessonId,))
        if new_lesson.poem:
            url = 'static/audio_poem'
            poem1 = new_lesson.poem.split('\n')
            poem = [item for item in poem1 if item.strip() != ""]
            for i in range(0, len(poem), 2):
                double_line = poem[i] + '\n' + poem[i + 1] if i + 1 < len(poem) else poem[i]
                cursor.execute(
                    'INSERT INTO lesson_poem (lesson_id, double_line) VALUES (?, ?);',
                    (new_lesson.lessonId, double_line))
                lesson_id = cursor.lastrowid
                double_line = double_line.split('\n')
                audio0 = main(double_line[0], url, f"{lesson_id}0v")
                audioURL1 = convert_wav_to_mp3(audio0, url)
                output_file = f"{lesson_id}.mp3"
                if i + 1 < len(poem):
                    audio1 = main(double_line[1], url, f"{lesson_id}1v")
                    audioURL2 = convert_wav_to_mp3(audio1, url)
                    concatenate_audio_with_pause([f'static/audio_poem/{audioURL1}', f'static/audio_poem/{audioURL2}'],
                                                 f'static/audio_poem/{output_file}')
                    os.remove(f'static/audio_poem/{audioURL2}')
                else:
                    concatenate_audio_with_pause([f'static/audio_poem/{audioURL1}'],
                                                 f'static/audio_poem/{output_file}')
                os.remove(f'static/audio_poem/{audioURL1}')

                cursor.execute('UPDATE lesson_poem SET audioURL = ? WHERE id = ?;',
                               (output_file, lesson_id))
            conn.commit()

        cursor.execute('DELETE FROM lesson_text WHERE lesson_id = ?;', (new_lesson.lessonId,))
        if new_lesson.reading:
            url = 'static/audio_text'

            reading = new_lesson.reading
            substrings_list = list(sentenize(reading))
            reading = [substring.text for substring in substrings_list]
            startTime = 0
            for line in reading:
                if contains_letters_or_digits(line):
                    cursor.execute(
                        'INSERT INTO lesson_text (lesson_id, line) VALUES (?, ?);',
                        (new_lesson.lessonId, line))
                    lesson_id = cursor.lastrowid
                    audioURL = main(line, url, lesson_id)
                    audioURL = convert_wav_to_mp3(audioURL, url)
                    endTime = startTime + get_audio_length(f'{url}/{audioURL}')
                    cursor.execute('UPDATE lesson_text SET startTime = ?, endTime = ?, audioURL = ? WHERE id = ?;',
                                   (startTime, endTime, audioURL, lesson_id))
                    startTime = endTime + 400
                else:
                    continue
            conn.commit()

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        # Если произошла ошибка, откатываем изменения
        logger.error(f"Ошибка: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False


def check_image(words):
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    sql_query = '''
        SELECT word
        FROM words_data
        WHERE word IN ({})
        AND image IS NULL;
    '''.format(', '.join(['?'] * len(words)))

    # Выполняем запрос
    cursor.execute(sql_query, words)

    # Получаем результат
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


def task_result(result: ResultGame, userId):
    try:
        conn = sqlite3.connect('text.db')
        cursor = conn.cursor()
        now = datetime.now(timezone.utc)
        date_solving = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        cursor.execute(
            'INSERT INTO solving_result (lesson_id, student_id, item_id, job_type, results, date_solving) VALUES (?, ?, ?, ?, ?, ?);',
            (result.lessonId, userId, result.item_id, result.exerciseType, result.result, date_solving))
        conn.commit()
        cursor.close()
        conn.close()
        return JSONResponse(status_code=200, content={"message": ''})
    except:
        return JSONResponse(status_code=500, content={"message": ''})


def find_nested_list(lst, num):
    for sublist in lst:
        for pair in sublist:
            if pair[1] == num:
                return sublist
    return None


def clone_class(classId: EntityId, userId: int):
    lesson_word_list = []
    lesson_sentences_list = []
    lesson_text_list = []
    lesson_poem_list = []
    conn = sqlite3.connect('text.db')
    cursor = conn.cursor()
    class_title = cursor.execute('SELECT title FROM class_list WHERE id = ?;', (classId.id,)).fetchone()
    lesson_list = cursor.execute('SELECT * FROM lessons_list WHERE class_id = ?;', (classId.id,)).fetchall()
    if lesson_list:
        for i in range(len(lesson_list)):
            lesson_word_list.append(cursor.execute('SELECT * FROM lesson_word WHERE lesson_id = ?;',
                                                   (lesson_list[i][0],)).fetchall())
            lesson_sentences_list.append(cursor.execute('SELECT * FROM lesson_sentences WHERE lesson_id = ?;',
                                                        (lesson_list[i][0],)).fetchall())
            lesson_text_list.append(cursor.execute('SELECT * FROM lesson_text WHERE lesson_id = ?;',
                                                   (lesson_list[i][0],)).fetchall())
            lesson_poem_list.append(cursor.execute('SELECT * FROM lesson_poem WHERE lesson_id = ?;',
                                                   (lesson_list[i][0],)).fetchall())
    cursor.execute('INSERT INTO class_list (title, teacher_id) VALUES (?, ?);',
                   (f"клон {class_title[0]}", userId))
    new_class_id = cursor.lastrowid
    conn.commit()

    for lesson in lesson_list:
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