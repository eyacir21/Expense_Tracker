from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from models import Users
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated
from passlib.context import CryptContext
from database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt
from datetime import timedelta, timezone, datetime


router = APIRouter(prefix='/auth', tags=['Authentication'])

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
OAuth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/login')

SECRET_KEY = 'f91a5a9396654287712050800deec96ee25d0936ffb45453f562663d6ff2a7c1'
ALGORITHOM = 'HS256'


class CreateUsers(BaseModel):
    email: str
    username: str
    password: str = Field(min_length=4)


def authenticate_user(username, password, db):
    user = db.query(Users).filter(Users.username == username).first()

    if user is None:
        return False

    if bcrypt_context.verify(password, user.hash_password):
        return user

    return False


def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})

    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHOM)


def get_current_user(
    token: Annotated[str, Depends(OAuth2_bearer)]
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHOM])

        username: str = payload.get('sub')
        user_id: int = payload.get('id')

        if username is None or user_id is None:
            raise HTTPException(status_code=404, detail='User not found')

        return {'username': username, 'id': user_id}

    except Exception:
        raise HTTPException(status_code=404, detail='User not found')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.post('/register')
def create_user(db: db_dependency, new_users: CreateUsers):
    username_exists = db.query(Users).filter(
        Users.username == new_users.username
    ).first()

    if username_exists is not None:
        raise HTTPException(status_code=400, detail='Username already exists')

    email_exists = db.query(Users).filter(
        Users.email == new_users.email
    ).first()

    if email_exists is not None:
        raise HTTPException(status_code=400, detail='Email already exists')

    user_model = Users(
        email=new_users.email,
        username=new_users.username,
        hash_password=bcrypt_context.hash(new_users.password)
    )

    db.add(user_model)
    db.commit()
    db.refresh(user_model)

    return JSONResponse(
        status_code=201,
        content={
            'id': user_model.id,
            'username': user_model.username,
            'email': user_model.email
        }
    )


@router.post('/login')
def login_user(
    db: db_dependency,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(
            status_code=401,
            detail='Invalid username or password'
        )

    token = create_access_token(
        user.username,
        user.id,
        timedelta(minutes=30)
    )

    return {'access_token': token, 'token_type': 'bearer'}
