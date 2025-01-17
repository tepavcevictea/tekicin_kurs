from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session

# Initialize the FastAPI application
app = FastAPI()

# Create all database tables defined in the models module using SQLAlchemy
models.Base.metadata.create_all(bind=engine) #create all of the tables in postgres

# Define the schema for a single choice in a question
class ChoiceBase(BaseModel):
    choice_text: str
    is_correct : bool

# Define the schema for a question, which includes a list of choices
class QuestionBase(BaseModel):
    question_text: str
    choices: List[ChoiceBase]


# Dependency to get a database session
def get_db():
    db= SessionLocal() # Create a new database session
    try:
        yield db # Yield the session to be used in a request
    finally:
        db.close() # Ensure the session is closed after the request

# Annotate the dependency for database session injection
db_dependency = Annotated[Session, Depends(get_db)]

@app.get("/questons/{question_id}")
async def read_question(question_id: int, db:db_dependency):
    result = db.query(models.Questions).filter(models.Questions.id==question_id).first()
    if not result:
        raise HTTPException(status_code=404, detail='Question not found')
    return result

@app.get("/choices/{question_id}")
async def read_choices(question_id: int, db:db_dependency):
        result = db.query(models.Choices).filter(models.Choices.question_id==question_id).all()
        if not result:
            raise HTTPException(status_code=404, detail='Question not found')
        return result





# Endpoint to create a new question with associated choices
@app.post("/questions/")
async def create_questions(question: QuestionBase, db: db_dependency):
    db_question = models.Questions(question_text=question.question_text)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    # Loop through the choices in the request to add them to the database
    for choice in question.choices:
        db_choice = models.Choices(choice_text=choice.choice_text, is_correct=choice.is_correct, question_id=db_question.id)
        db.add(db_choice)
    db.commit()

