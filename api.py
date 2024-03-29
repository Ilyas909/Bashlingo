from pydantic import BaseModel
from typing import Optional
from fastapi import UploadFile, File


class Login(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str


class UserID(BaseModel):
    id: int


class User(BaseModel):
    username: str


class NewName(BaseModel):
    newName: str


class NewClass(BaseModel):
    title: str
    studentsList: str


class NewNameStudent(BaseModel):
    classId: int
    studentId: int
    newName: str


class EntityId(BaseModel):
    id: int



class Entityt(BaseModel):
    lessonId: int
    available: bool


class AudioFile(BaseModel):
    correct_text: str
    audio: UploadFile = File(...)


class GetWords(BaseModel):
    theme: str
    existingWords: Optional[str] = None
    words: Optional[str] = None
    sentences: Optional[str] = None
    poem: Optional[str] = None
    reading: Optional[str] = None
    classId: Optional[int] = None
    lessonId: Optional[int] = None
    date: Optional[str] = None
    enabledTasks: Optional[list] = None


class ResultGame(BaseModel):
    lessonId: int     #Id урока
    item_id: int      #Id предложения или слова,
    exerciseType: str #тип задания
    result: bool      #результат


class NewStudent(BaseModel):
    classId: int
    studentName: str
