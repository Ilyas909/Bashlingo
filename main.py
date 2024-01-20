from fastapi import FastAPI, Cookie, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from api import Login, UserID, NewClass, ClassID, NewName, NewNameStudent, EntityId, GetWords
from bd import user_exists_by_credentials, get_user_by_id, get_clssList_by_teacherID, add_new_classdb, \
    add_new_studentdb, get_class_info_by_id, update_class_namedb, update_student_namedb, delete_student, \
    get_class_lessons_by_id, add_lesson, get_lessons_by_studentId, get_lesson_menu_by_lessonId

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

client = ''
role = ''
teacherID = 1
studentID = 1

session_storage = {}


def get_current_user(cookie: str = Cookie(default=None)):
    # Получаем пользователя по значению куки
    user_id, role = session_storage.get(cookie, (None, None))
    if user_id is None or role is None:
        return None, None
    return UserID(id=user_id), role


@app.post("/auth/login")
def authentication(login: Login):
    global client, role, teacherID, studentID
    client, role = user_exists_by_credentials(login)
    if not client:
        return JSONResponse(status_code=404, content={"message": "not found"})
    if role == 'teacher':
        teacherID = client[0]
    elif role == 'student':
        studentID = client[0]

    session_id = str(hash((client[0], role)))
    session_storage[session_id] = (client[0], role)

    response = JSONResponse(content={"id": client[0], "username": client[3], "avatar": client[2], "role": role})
    response.set_cookie(key="session", value=session_id)

    return response


@app.post("/auth/me")
def auth():
    userID: UserID = get_current_user()
    inf_user = get_user_by_id(userID, role)
    return {"id": inf_user[0], "username": inf_user[3], "avatar": inf_user[2], "role": role}


@app.post("/user")
def get_user_data(userID: UserID):
    inf_user = get_user_by_id(userID, role)
    return {"id": inf_user[0], "username": inf_user[3], "avatar": inf_user[2], "role": role}


@app.get("/classes/get-classes-list")
def get_classes_list():
    global teacherID
    list_class = get_clssList_by_teacherID(teacherID)
    return {"classesList": list_class}


@app.put("/classes/add-class")
def add_new_class(new_class: NewClass):
    global teacherID
    new_class.studentsList=new_class.studentsList.split(',')
    id_add_class = add_new_classdb(new_class, teacherID)
    if id_add_class:
        add_student = add_new_studentdb(new_class, id_add_class)
        if add_student:
            list_class = get_clssList_by_teacherID(teacherID)
            return {"classesList": list_class}
        else:
            return JSONResponse(status_code=404, content={"message": "not found"})
    else:
        return JSONResponse(status_code=404, content={"message": "not found"})


@app.put("/classes/get-class")
def get_class_by_id(class_id: ClassID):
    return get_class_info_by_id(class_id)


@app.put("/classes/update-class-name/{classId}")
def update_class_name(classId: int, new_name: NewName):
    res = update_class_namedb(classId, new_name)
    if not res:
        return JSONResponse(status_code=500, content={"message": "Не удалось обновить название класса"})
    return JSONResponse(status_code=200, content={"message": "Название класса обнавлено"})


@app.put("/classes/update-student-name")
def update_student_name(new_name_student: NewNameStudent):
    res = update_student_namedb(new_name_student)
    return res

@app.delete("/classes/delete-student/{studentId}")
def delete_studentID(studentId: int):
    res = delete_student(studentId)
    if not res:
        return JSONResponse(status_code=500, content={"message": "Не удалось удалить студента"})
    return JSONResponse(status_code=200, content={"message": "Студент удален"})


@app.put("/classes/get-class-lessons")
def fetch_class_lessons(classId: EntityId):
    res = get_class_lessons_by_id(classId)
    return res


@app.post("/generate/words")
def get_create_lesson_words(words: GetWords):
    if words.existingWords:
        generate_words = words.existingWords + ", lion,tiger,elephant"
    else:
        generate_words = "lion,tiger,elephant"
    wrongWords = "carrot,apple"
    return {"words": generate_words, "wrongWords": wrongWords}


@app.post("/generate/sentences")
def get_create_lesson_sentences(sentences: GetWords):
    return {"sentences": "The tree stood tall by the riverbank. The waterfall cascaded down with a roar."}


@app.put("/generate/create-lesson")
def create_lesson(lessonData: GetWords):
    res = add_lesson(lessonData)
    if not res:
        return JSONResponse(status_code=500, content={"message": "Не удалось добавить урок"})
    return JSONResponse(status_code=200, content={"message": "Урок добавлен"})



@app.get("/lessons-list")
def create_item():
    lesson_list = get_lessons_by_studentId(studentID)
    return lesson_list


@app.get("/lesson-menu/{lessonId}")
def get_lesson_menu(lessonId: int):
    lesson_menu = get_lesson_menu_by_lessonId(lessonId)
    return lesson_menu