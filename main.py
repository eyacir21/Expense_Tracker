from fastapi import FastAPI, Depends, HTTPException
import models
from models import Transactions, Users
from sqlalchemy.orm import Session
from typing import Annotated
from database import engine, SessionLocal
from fastapi.responses import JSONResponse
from router import auth, transactions
from router.auth import get_current_user


app = FastAPI()


models.Base.metadata.create_all(bind=engine)
app.include_router(auth.router)
app.include_router(transactions.router)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@app.get('/')
def read_home():
    return {'message': 'Expense Tracker API is running'}


@app.get('/user')
def get_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    return db.query(Users).filter(Users.id == user.get('id')).first()
