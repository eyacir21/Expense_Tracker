from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated, Optional
from datetime import date as Date

from database import SessionLocal
from models import Transactions
from router.auth import get_current_user


router = APIRouter(prefix='/transactions', tags=['Transactions'])

class Transaction(BaseModel):
    title: str
    amount: float = Field(gt=0)
    type: str
    category: str
    date: Date


class TransactionUpdate(BaseModel):
    title: Optional[str] = Field(default=None)
    amount: Optional[float] = Field(default=None, gt=0)
    type: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None)
    date: Optional[Date] = Field(default=None)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.post('')
def create_transaction(
    user: user_dependency,
    db: db_dependency,
    new_transaction: Transaction
):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    if new_transaction.type not in ['income', 'expense']:
        raise HTTPException(
            status_code=400,
            detail='type must be income or expense'
        )

    transaction_model = Transactions(
        **new_transaction.model_dump(),
        owner_id=user.get('id')
    )

    db.add(transaction_model)
    db.commit()
    db.refresh(transaction_model)

    return transaction_model


@router.get('')
def read_transactions(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    return db.query(Transactions).filter(
        Transactions.owner_id == user.get('id')
    ).all()


@router.get('/filter')
def filter_transactions(
    user: user_dependency,
    db: db_dependency,
    type: Optional[str] = None,
    category: Optional[str] = None,
    minimum_amount: Optional[float] = None,
    maximum_amount: Optional[float] = None
):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    query = db.query(Transactions).filter(
        Transactions.owner_id == user.get('id')
    )

    if type is not None:
        query = query.filter(Transactions.type == type)

    if category is not None:
        query = query.filter(Transactions.category == category)

    if minimum_amount is not None:
        query = query.filter(Transactions.amount >= minimum_amount)

    if maximum_amount is not None:
        query = query.filter(Transactions.amount <= maximum_amount)

    return query.all()


@router.get('/{transaction_id}')
def read_specific_transaction(
    user: user_dependency,
    db: db_dependency,
    transaction_id: int
):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    specific_transaction = db.query(Transactions).filter(
        Transactions.owner_id == user.get('id')
    ).filter(
        Transactions.id == transaction_id
    ).first()

    if specific_transaction is not None:
        return specific_transaction

    raise HTTPException(status_code=404, detail='Transaction not found')


@router.put('/{transaction_id}')
def update_transaction(
    user: user_dependency,
    db: db_dependency,
    transaction_id: int,
    update_transaction_data: TransactionUpdate
):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    transaction = db.query(Transactions).filter(
        Transactions.owner_id == user.get('id')
    ).filter(
        Transactions.id == transaction_id
    ).first()

    if transaction is None:
        raise HTTPException(status_code=404, detail='Transaction not found')

    update_data = update_transaction_data.model_dump(exclude_unset=True)

    if 'type' in update_data and update_data['type'] not in ['income', 'expense']:
        raise HTTPException(
            status_code=400,
            detail='type must be income or expense'
        )

    for key, value in update_data.items():
        setattr(transaction, key, value)

    db.commit()
    db.refresh(transaction)

    return transaction


@router.delete('/{transaction_id}')
def delete_transaction(
    user: user_dependency,
    db: db_dependency,
    transaction_id: int
):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    transaction = db.query(Transactions).filter(
        Transactions.owner_id == user.get('id')
    ).filter(
        Transactions.id == transaction_id
    ).first()

    if transaction is None:
        raise HTTPException(status_code=404, detail='Transaction not found')

    db.query(Transactions).filter(
        Transactions.owner_id == user.get('id')
    ).filter(
        Transactions.id == transaction_id
    ).delete()

    db.commit()

    return JSONResponse(
        status_code=200,
        content={'message': 'Transaction deleted successfully'}
    )
