from pydantic import BaseModel
from typing import Optional

class Login(BaseModel):
    username: str
    password: str


class UserID(BaseModel):
    id: int


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


class GetWords(BaseModel):
    theme: str
    existingWords: Optional[str] = None
    words: Optional[str] = None
    sentences: Optional[str] = None
    poem: Optional[str] = None
    reading: Optional[str] = None
    classId: Optional[int] = None
    date: Optional[str] = None
