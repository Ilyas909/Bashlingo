import os
from json import JSONDecodeError
import shutil
from fastapi import FastAPI, Depends, UploadFile, File
from fastapi import Form
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.requests import Request
from api import Login, UserID, NewClass, NewName, NewNameStudent, EntityId, GetWords, Entityt, User, AudioFile, \
    ResultGame
from bd import user_exists_by_credentials, get_user_by_id, get_clssList_by_teacherID, add_new_classdb, \
    add_new_studentdb, get_class_info_by_id, update_class_namedb, update_student_namedb, delete_student, \
    get_class_lessons_by_id, add_lesson, get_lessons_by_studentId, get_lesson_menu_by_lessonId, get_lesson_by_id, \
    lesson_availability, delete_lesson_by_id, fetch_lesson_results, username_update, get_username, save_avatar, \
    check_student, image_words, get_poem_audio, get_text_audio, edit_lesson_lessonId, check_image, get_sentence, \
    get_speaking, task_result
import json
from fastapi.staticfiles import StaticFiles
from email import message_from_bytes
from email.policy import HTTP

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# Настройка CORS
origins = [
    "http://localhost:3000"  # Если ваш React-приложение работает на этом порту
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все HTTP-методы (GET, POST, etc.)
    allow_headers=["*"],  # Разрешить все заголовки
)


try:
    with open("config.json", "r") as file:
        inf = json.load(file)
        url_server = inf["url_server"]
        user_is_secure = inf["user_is_secure"]
except (FileNotFoundError, json.decoder.JSONDecodeError):
    raise JSONDecodeError("config.json not found")



session_storage = {}

# Имя файла, в котором будем сохранять информацию о сессиях
SESSION_FILE = "session_data.json"

# Загрузка информации о сессиях из файла
try:
    with open(SESSION_FILE, "r") as file:
        session_storage = json.load(file)
except (FileNotFoundError, json.decoder.JSONDecodeError):
    session_storage = {}


def save_session_data():
    # Сохранение информации о сессиях в файл
    with open(SESSION_FILE, "w") as file:
        json.dump(session_storage, file)


def get_current_user(request: Request):
    cookie_session = request.cookies.get("session")
    print('cookie_session=', cookie_session)
    # Получаем пользователя по значению куки
    user_id, role = session_storage.get(cookie_session, (None, None))
    if user_id is None or role is None:
        return JSONResponse(status_code=404, content={"message": "not found"}), None
    return UserID(id=user_id), role


def get_current_teacher(request: Request):
    userId, role = get_current_user(request)
    if role == 'teacher':
        return userId.id
    else:
        return JSONResponse(status_code=404, content={"message": "not found"})


def get_current_student(request: Request):
    userId, role = get_current_user(request)
    if role == 'student':
        return userId.id
    else:
        return JSONResponse(status_code=404, content={"message": "not found"})


@app.get("/auth/me")
def auth(userID: UserID = Depends(get_current_user)):
    if isinstance(userID[0], JSONResponse):
        return userID[0]
    inf_user = get_user_by_id(userID[0], userID[1])
    if userID[1] == 'student':
        return {"id": inf_user[0], "username": inf_user[4], "avatar": inf_user[3], "role": userID[1]}
    elif userID[1] == 'teacher':
        return {"id": inf_user[0], "username": inf_user[3], "avatar": inf_user[2], "role": userID[1]}


@app.post("/auth/login")
def authentication(login: Login):
    login.username = login.email
    client, role = user_exists_by_credentials(login)
    if not client:
        return JSONResponse(status_code=404, content={"message": "not found"})

    session_id = str(hash((client[0], role)))
    session_storage[session_id] = (client[0], role)

    if role == "teacher":
        response = JSONResponse(content={"id": client[0], "username": client[3], "avatar": client[2], "role": role})
        if user_is_secure:
            response.set_cookie(key="session", value=session_id, httponly=True, samesite="None", secure=True)
        else:
            response.set_cookie(key="session", value=session_id)

    elif role == "student":
        response = JSONResponse(content={"id": client[0], "username": client[4], "avatar": client[3], "role": role})
        if user_is_secure:
            response.set_cookie(key="session", value=session_id, httponly=True, samesite="None", secure=True)
        else:
            response.set_cookie(key="session", value=session_id)
    save_session_data()
    return response


@app.post('/user/logout')
def user_logout(request: Request):
    userId, role = get_current_user(request)
    if userId and role:
        global session_storage
        cookie_session = request.cookies.get("session")
        if cookie_session in session_storage:
            del session_storage[cookie_session]

        with open(SESSION_FILE, 'w') as file:
            json.dump(session_storage, file, indent=2)


@app.post("/user")
def get_user_data(userID: UserID, request: Request):
    userId, role = get_current_user(request)
    userId = userId.id
    if role and userId:
        inf_user = get_user_by_id(userID, role)
        return {"id": inf_user[0], "username": inf_user[3], "avatar": inf_user[2], "role": role}
    else:
        return JSONResponse(status_code=404, content={"message": "not found"})


@app.get("/classes/get-classes-list")
def get_classes_list(request: Request):
    userId = get_current_teacher(request)
    if not isinstance(userId, JSONResponse):
        list_class = get_clssList_by_teacherID(userId)
        return {"classesList": list_class}
    else:
        return userId


@app.put("/classes/add-class")
def add_new_class(new_class: NewClass, request: Request):
    userId = get_current_teacher(request)
    if not isinstance(userId, JSONResponse):
        new_class.studentsList = new_class.studentsList.split(', ')
        id_add_class = add_new_classdb(new_class, userId)
        if id_add_class:
            add_student = add_new_studentdb(new_class, id_add_class)
            if add_student:
                list_class = get_clssList_by_teacherID(userId)
                return {"classesList": list_class}
            else:
                return JSONResponse(status_code=404, content={"message": "not found"})
        else:
            return JSONResponse(status_code=404, content={"message": "not found"})
    else:
        return userId


@app.get("/classes/get-class/{class_id}")
def get_class_by_id(class_id: int, request: Request):
    userId = get_current_teacher(request)
    if not isinstance(userId, JSONResponse):
        return get_class_info_by_id(EntityId(id=class_id))
    else:
        return userId


@app.put("/classes/update-class-name/{classId}")
def update_class_name(classId: int, new_name: NewName, request: Request):
    userId = get_current_teacher(request)
    if not isinstance(userId, JSONResponse):
        res = update_class_namedb(classId, new_name)
        if not res:
            return JSONResponse(status_code=500, content={"message": "Не удалось обновить название класса"})
        return JSONResponse(status_code=200, content={"message": "Название класса обнавлено"})
    else:
        return userId


@app.put("/classes/update-student-name")
def update_student_name(new_name_student: NewNameStudent, request: Request):
    userId = get_current_teacher(request)
    if not isinstance(userId, JSONResponse):
        res = update_student_namedb(new_name_student)
        return res
    else:
        return userId


@app.delete("/classes/delete-student/{studentId}")
def delete_studentID(studentId: int, request: Request):
    userId = get_current_teacher(request)
    if not isinstance(userId, JSONResponse):
        res = delete_student(studentId)
        if not res:
            return JSONResponse(status_code=500, content={"message": "Не удалось удалить студента"})
        return JSONResponse(status_code=200, content={"message": "Студент удален"})
    else:
        return userId


@app.get("/classes/get-class-lessons/{classId}")
def fetch_class_lessons(classId: int, request: Request):
    userId = get_current_teacher(request)
    if not isinstance(userId, JSONResponse):
        res = get_class_lessons_by_id(EntityId(id=classId))
        return res
    else:
        return userId


@app.post("/generate/words")
def get_create_lesson_words(words: GetWords, request: Request):
    userId = get_current_teacher(request)
    if not isinstance(userId, JSONResponse):
        if words.existingWords:
            generate_words = words.existingWords + ", Атайым, әҙәбиәт, донъяһына, килде, күренде, балҡыны, донъяға, һоҡланды, бик, күптәрҙе, таң"
        else:
            generate_words = "Атайым, әҙәбиәт, донъяһына, килде, күренде, балҡыны, донъяға, һоҡланды, бик, күптәрҙе, таң"

        words = generate_words.lower().split(', ')
        wrongWords = check_image(words)
        wrongWords = [str(word[0]) for word in wrongWords]
        wrongWords = ', '.join(wrongWords)
        return {"words": generate_words, "wrongWords": wrongWords}
    return userId


@app.post("/generate/sentences")
def get_create_lesson_sentences(sentences: GetWords, request: Request):
    userId = get_current_teacher(request)
    if not isinstance(userId, JSONResponse):
        return {"sentences": "The tree stood tall by the riverbank. The waterfall cascaded down with a roar."}
    return userId


@app.put("/generate/create-lesson")
def create_lesson(lessonData: GetWords, request: Request):
    userId = get_current_teacher(request)
    if not isinstance(userId, JSONResponse):
        res = add_lesson(lessonData)
        if not res:
            return JSONResponse(status_code=500, content={"message": "Не удалось добавить урок"})
        return JSONResponse(status_code=200, content={"message": "Урок добавлен"})
    else:
        return userId


@app.get("/classes/fetch-lesson/{lessonId}")
def fetch_lesson_by_Id(lessonId: int, request: Request):
    userId = get_current_teacher(request)
    if not isinstance(userId, JSONResponse):
        res = get_lesson_by_id(lessonId)
        return res
    else:
        return userId


@app.post("/classes/update-lesson")
def set_lesson_availability(availability: Entityt, request: Request):
    userId = get_current_teacher(request)
    if not isinstance(userId, JSONResponse):
        res = lesson_availability(availability)
        return res
    else:
        return userId


@app.delete('/classes/delete-lesson/{lessonId}/{classId}')
def delete_lesson(lessonId: int, classId: int, request: Request):
    userId = get_current_teacher(request)
    if not isinstance(userId, JSONResponse):
        res = delete_lesson_by_id(lessonId, classId)
        return res
    else:
        return userId


@app.get('/classes/get-lesson-results/{lessonId}')
def fetch_lesson_results_by_Id(lessonId: int, request: Request):
    userId = get_current_teacher(request)
    if not isinstance(userId, JSONResponse):
        res = fetch_lesson_results(EntityId(id=lessonId))
        return res
    else:
        return userId


@app.put('/generate/edit-lesson')
def edit_lesson(edit: GetWords, request: Request):
    userId = get_current_teacher(request)
    if not isinstance(userId, JSONResponse):
        res = edit_lesson_lessonId(edit)
        if not res:
            return JSONResponse(status_code=500, content={"message": "Не удалось изменить урок"})
        return JSONResponse(status_code=200, content={"message": "Урок изменен"})
    else:
        return userId


@app.put('/user/username')
def update_username(username: User, request: Request):
    userId = get_current_student(request)
    if not isinstance(userId, JSONResponse):
        res = username_update(userId, username.username)
        return res
    else:
        return userId


@app.post("/user/photo")
def create_upload_file(request: Request, file: UploadFile = File(...)):
    userId = get_current_student(request)
    if not isinstance(userId, JSONResponse):
        username = get_username(userId)
        file_path = f"static/avatar/{username}"
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        res = save_avatar(userId, file_path)
        return res


def compliance_check(lessonId, request: Request):
    userId = get_current_student(request)
    if not isinstance(userId, JSONResponse):
        res = check_student(userId, lessonId)
        return res
    else:
        return False


@app.get('/tasks/correspondence/{lessonId}')
def get_correspondence_tasks(lessonId: int, request: Request):
    userId = get_current_student(request)
    check = compliance_check(lessonId, request)
    if check:
        res = image_words(lessonId, userId)
        return res
    return JSONResponse(status_code=500, content={"message": 'пользователь не авторизован'})


@app.get('/tasks/sentence/{lessonId}')
def get_sentence_tasks(lessonId: int, request: Request):
    userId = get_current_student(request)
    check = compliance_check(lessonId, request)
    if check:
        res = get_sentence(lessonId, userId)
        return res
    return JSONResponse(status_code=404, content={"message": 'пользователь не авторизован'})


@app.get('/tasks/speaking/{lessonId}')
def get_speaking_tasks(lessonId: int, request: Request):
    userId = get_current_student(request)
    check = compliance_check(lessonId, request)
    if check:
        res = get_speaking(lessonId, userId)
        return res
    return JSONResponse(status_code=404, content={"message": 'пользователь не авторизован'})




@app.post('/tasks/speaking')
async def send_speaking_answer(request: Request, correct_text: str = Form(...),
    audio: UploadFile = File(...)):
    userId = get_current_student(request)
    if not isinstance(userId, JSONResponse):
        # Получение значений
        audio_data = audio.file.read()
        # Сохранение файла на сервере
        file_location = f"./static/audio_word_task/{correct_text}.wav"
        with open(file_location, "wb") as file:
            file.write(audio_data)

    return {"result": "OK"}


@app.get('/tasks/poem/{lessonId}')
def get_poem(lessonId: int, request: Request):
    check = compliance_check(lessonId, request)
    check = 1
    if check:
        res = get_poem_audio(lessonId)
        return res
    return JSONResponse(status_code=500, content={"message": 'пользователь не авторизован'})


@app.get('/tasks/text/{lessonId}')
def get_text(lessonId: int, request: Request):
    check = compliance_check(lessonId, request)
    if check:
        res = get_text_audio(lessonId)
        return res
    return JSONResponse(status_code=500, content={"message": 'пользователь не авторизован'})


@app.get("/lessons-list")
def create_item(request: Request):
    userId = get_current_student(request)
    if not isinstance(userId, JSONResponse):
        lesson_list = get_lessons_by_studentId(userId)
        return lesson_list
    else:
        return userId


@app.get("/lesson-menu/{lessonId}")
def get_lesson_menu(lessonId: int, request: Request):
    userId = get_current_user(request)
    if not isinstance(userId, JSONResponse):
        lesson_menu = get_lesson_menu_by_lessonId(lessonId, userId[0].id)
        return lesson_menu
    else:
        return userId

@app.put('/tasks/sentence/result')
def result_tasks(result: ResultGame, request: Request):
    userId = get_current_student(request)
    if not isinstance(userId, JSONResponse):
        res = task_result(result, userId)
        return res
    else:
        return userId


import os
from typing import BinaryIO

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import StreamingResponse


def send_bytes_range_requests(
    file_obj: BinaryIO, start: int, end: int, chunk_size: int = 10_000
):
    """Send a file in chunks using Range Requests specification RFC7233

    `start` and `end` parameters are inclusive due to specification
    """
    with file_obj as f:
        f.seek(start)
        while (pos := f.tell()) <= end:
            read_size = min(chunk_size, end + 1 - pos)
            yield f.read(read_size)


def _get_range_header(range_header: str, file_size: int) -> tuple[int, int]:
    def _invalid_range():
        return HTTPException(
            status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
            detail=f"Invalid request range (Range:{range_header!r})",
        )

    try:
        h = range_header.replace("bytes=", "").split("-")
        start = int(h[0]) if h[0] != "" else 0
        end = int(h[1]) if h[1] != "" else file_size - 1
    except ValueError:
        raise _invalid_range()

    if start > end or start < 0 or end > file_size - 1:
        raise _invalid_range()
    return start, end


def range_requests_response(
    request: Request, file_path: str, content_type: str
):
    """Returns StreamingResponse using Range Requests of a given file"""

    file_size = os.stat(file_path).st_size
    range_header = request.headers.get("range")

    headers = {
        "content-type": content_type,
        "accept-ranges": "bytes",
        # "content-encoding": "identity",
        "content-length": str(file_size),
        "access-control-expose-headers": (
            "content-type, accept-ranges, content-length, "
            "content-range, content-encoding"
        ),
    }
    start = 0
    end = file_size - 1
    status_code = status.HTTP_200_OK

    if range_header is not None:
        start, end = _get_range_header(range_header, file_size)
        size = end - start + 1
        headers["content-length"] = str(size)
        headers["content-range"] = f"bytes {start}-{end}/{file_size}"
        status_code = status.HTTP_206_PARTIAL_CONTENT

    return StreamingResponse(
        send_bytes_range_requests(open(file_path, mode="rb"), start, end),
        headers=headers,
        status_code=status_code,
    )



@app.get("/big_audio/{lessonId}")
def get_video(lessonId:int, request: Request):
    return range_requests_response(
        request, file_path=f"static/audio_big_text/{lessonId}", content_type="audio/mpeg"
    )