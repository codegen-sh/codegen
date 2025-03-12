from pydantic import BaseModel
from typing import List, Optional

class PublisherBase(BaseModel):
    name: str

class PublisherCreate(PublisherBase):
    pass

class Publisher(PublisherBase):
    id: int
    books: List["Book"] = []

    class Config:
        orm_mode = True

class BookBase(BaseModel):
    title: str
    author: str
    description: str
    publisher_id: Optional[int]

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: int
    publisher: Optional[Publisher]

    class Config:
        orm_mode = True
