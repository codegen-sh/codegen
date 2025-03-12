# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import schemas
from database import SessionLocal, engine
from typing import List

# Initialize the app and create database tables
app = FastAPI()
models.Base.metadata.create_all(bind=engine)

# Dependency for the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utility Functions
def get_book_or_404(book_id: int, db: Session):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

# CRUD Operations

@app.post("/books/", response_model=schemas.Book)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    db_book = models.Book(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.get("/books/", response_model=List[schemas.Book])
def read_books(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    books = db.query(models.Book).offset(skip).limit(limit).all()
    return books

@app.get("/books/{book_id}", response_model=schemas.Book)
def read_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@app.put("/books/{book_id}", response_model=schemas.Book)
def update_book(book_id: int, book: schemas.BookCreate, db: Session = Depends(get_db)):
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    for key, value in book.dict().items():
        setattr(db_book, key, value)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.delete("/books/{book_id}", response_model=schemas.Book)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(db_book)
    db.commit()
    return db_book

@app.post("/publishers/", response_model=schemas.Publisher)
def create_publisher(publisher: schemas.PublisherCreate, db: Session = Depends(get_db)):
    db_publisher = models.Publisher(**publisher.dict())
    db.add(db_publisher)
    db.commit()
    db.refresh(db_publisher)
    return db_publisher

@app.get("/publishers/", response_model=List[schemas.Publisher])
def read_publishers(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    publishers = db.query(models.Publisher).offset(skip).limit(limit).all()
    return publishers

@app.get("/publishers/{publisher_id}", response_model=schemas.Publisher)
def read_publisher(publisher_id: int, db: Session = Depends(get_db)):
    publisher = db.query(models.Publisher).filter(models.Publisher.id == publisher_id).first()
    if not publisher:
        raise HTTPException(status_code=404, detail="Publisher not found")
    return publisher

@app.put("/publishers/{publisher_id}", response_model=schemas.Publisher)
def update_publisher(publisher_id: int, publisher: schemas.PublisherCreate, db: Session = Depends(get_db)):
    db_publisher = db.query(models.Publisher).filter(models.Publisher.id == publisher_id).first()
    if not db_publisher:
        raise HTTPException(status_code=404, detail="Publisher not found")
    for key, value in publisher.dict().items():
        setattr(db_publisher, key, value)
    db.commit()
    db.refresh(db_publisher)
    return db_publisher

@app.delete("/publishers/{publisher_id}", response_model=schemas.Publisher)
def delete_publisher(publisher_id: int, db: Session = Depends(get_db)):
    db_publisher = db.query(models.Publisher).filter(models.Publisher.id == publisher_id).first()
    if not db_publisher:
        raise HTTPException(status_code=404, detail="Publisher not found")
    db.delete(db_publisher)
    db.commit()
    return db_publisher
