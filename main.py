from fastapi import FastAPI, Cookie, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.requests import Request
from api import Login, UserID, NewClass, ClassID, NewName, NewNameStudent, EntityId, GetWords, Entityt, User
from bd import user_exists_by_credentials, get_user_by_id, get_clssList_by_teacherID, add_new_classdb, \
    add_new_studentdb, get_class_info_by_id, update_class_namedb, update_student_namedb, delete_student, \
    get_class_lessons_by_id, add_lesson, get_lessons_by_studentId, get_lesson_menu_by_lessonId, get_lesson_by_id, \
    lesson_availability, delete_lesson_by_id, fetch_lesson_results, username_update, get_username, save_avatar, \
    check_student, image_words, get_poem_audio, get_text_audio, edit_lesson_lessonId
import json


app = FastAPI()

# Настройка CORS
origins = [
    "http://localhost:3000",  # Если ваш React-приложение работает на этом порту
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все HTTP-методы (GET, POST, etc.)
    allow_headers=["*"],  # Разрешить все заголовки
)


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
    if userID is None:
        return False
    inf_user = get_user_by_id(userID[0], userID[1])
    if userID[1] == 'student':
        return {"id": inf_user[0], "username": inf_user[4], "avatar": inf_user[3], "role": userID[1]}
    elif userID[1] == 'teacher':
        return {"id": inf_user[0], "username": inf_user[3], "avatar": inf_user[2], "role": userID[1]}


@app.post("/auth/login")
def authentication(login: Login):
    login.username=login.email
    client, role = user_exists_by_credentials(login)
    if not client:
        return JSONResponse(status_code=404, content={"message": "not found"})

    session_id = str(hash((client[0], role)))
    session_storage[session_id] = (client[0], role)

    if role == "teacher":
        response = JSONResponse(content={"id": client[0], "username": client[3], "avatar": client[2], "role": role})
        response.set_cookie(key="session", value=session_id)
    elif role == "student":
        response = JSONResponse(content={"id": client[0], "username": client[4], "avatar": client[3], "role": role})
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
        new_class.studentsList = new_class.studentsList.split(',')
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


@app.put("/classes/get-class")
def get_class_by_id(class_id: ClassID, request: Request):
    userId = get_current_teacher(request)
    if not isinstance(userId, JSONResponse):
        return get_class_info_by_id(class_id)
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




@app.put("/classes/get-class-lessons")
def fetch_class_lessons(classId: EntityId, request: Request):
    userId = get_current_teacher(request)
    if not isinstance(userId, JSONResponse):
        res = get_class_lessons_by_id(classId)
        return res
    else:
        return userId


@app.post("/generate/words")
def get_create_lesson_words(words: GetWords, request: Request):
    userId = get_current_teacher(request)
    if not isinstance(userId, JSONResponse):
        if words.existingWords:
            generate_words = words.existingWords + ", lion, tiger, elephant"
        else:
            generate_words = "lion, tiger, elephant"
        wrongWords = "carrot,apple"
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
    #userId = get_current_teacher(request)
    userId = 1
    if not isinstance(userId, JSONResponse):
        res = get_lesson_by_id(lessonId)
        return res
    else:
        return userId


@app.post("/classes/update-lesson")
def set_lesson_availability(availability: Entityt, request: Request):
    # userId = get_current_teacher(request)
    userId = 1
    if not isinstance(userId, JSONResponse):
        res = lesson_availability(availability)
        return res
    else:
        return userId


@app.delete('/classes/delete-lesson/{lessonId}/{classId}')
def delete_lesson(lessonId: int, classId: int, request: Request):
    # userId = get_current_teacher(request)
    userId = 1
    if not isinstance(userId, JSONResponse):
        res = delete_lesson_by_id(lessonId, classId)
        return res
    else:
        return userId


@app.put('/classes/get-lesson-results')
def fetch_lesson_results_by_Id(lessonId: EntityId, request: Request):
    # userId = get_current_teacher(request)
    userId = 1
    if not isinstance(userId, JSONResponse):
        res = fetch_lesson_results(lessonId)
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
    userId = 1
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
    userId = 1
    if not isinstance(userId, JSONResponse):
        res = check_student(userId, lessonId)
        return res
    else:
        return False


@app.get('/tasks/correspondence/{lessonId}')
def get_correspondence_tasks(lessonId: int, request: Request):
    check = compliance_check(lessonId, request)
    if check:
        res = image_words(lessonId)
        return res
    return JSONResponse(status_code=500, content={"message": 'пользователь не авторизован'})


@app.post('/tasks/speaking')
def send_speaking_answer(request: Request, file: UploadFile = File(...)):
    userId = get_current_student(request)
    userId = 1
    if not isinstance(userId, JSONResponse):
        username = get_username(userId)
        file_path = f"static/speaking_answer/{username}.mp3"
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        return {"result": "OK"}
    else:
        return {"result": "BAD"}


@app.get('/tasks/poem/{lessonId}')
def get_poem(lessonId: int, request: Request):
    check = compliance_check(lessonId, request)
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
    userId= get_current_student(request)
    if not isinstance(userId, JSONResponse):
        lesson_list = get_lessons_by_studentId(userId)
        return lesson_list
    else:
        return userId


@app.get("/lesson-menu/{lessonId}")
def get_lesson_menu(lessonId: int, request: Request):
    userId = get_current_user(request)
    if not isinstance(userId, JSONResponse):
        lesson_menu = get_lesson_menu_by_lessonId(lessonId)
        return lesson_menu
    else:
        return userId
