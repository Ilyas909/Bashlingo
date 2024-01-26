from pydantic import BaseModel
from typing import Optional

class Login(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str


class UserID(BaseModel):
    id: int


class User(BaseModel):
    username: str


class ClassID(BaseModel):
    id: int


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
