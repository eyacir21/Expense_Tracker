from datetime import date

from test.test_main import client
from fastapi import status
from main import app
from router.auth import get_current_user
from database import SessionLocal
from models import Transactions, Users


def override_get_current_user():
    return {
        'id': 1,
        'username': 'testuser'
    }


def create_test_user():
    db = SessionLocal()

    user = db.query(Users).filter(Users.id == 1).first()

    if user is None:
        user = Users(
            id=1,
            username='testuser',
            email='testuser@example.com',
            hash_password='test'
        )
        db.add(user)
        db.commit()

    db.close()


def create_test_transaction():
    db = SessionLocal()

    transaction = Transactions(
        title='Testing',
        amount=250,
        type='expense',
        category='Food',
        date=date.today(),
        owner_id=1
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    transaction_id = transaction.id
    db.close()

    return transaction_id


create_test_user()
app.dependency_overrides[get_current_user] = override_get_current_user


def test_get_transactions():
    response = client.get('/transactions')
    assert response.status_code == status.HTTP_200_OK


def test_get_specific_transaction():
    transaction_id = create_test_transaction()

    response = client.get(f'/transactions/{transaction_id}')

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['id'] == transaction_id


def test_create_transaction():
    request_data = {
        'title': 'Lunch',
        'amount': 300,
        'type': 'expense',
        'category': 'Food',
        'date': str(date.today())
    }

    response = client.post('/transactions', json=request_data)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['title'] == 'Lunch'


def test_update_transaction():
    transaction_id = create_test_transaction()

    request_data = {
        'amount': 500,
        'category': 'Shopping'
    }

    response = client.put(
        f'/transactions/{transaction_id}',
        json=request_data
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['amount'] == 500
    assert response.json()['category'] == 'Shopping'


def test_delete_transaction():
    transaction_id = create_test_transaction()

    response = client.delete(f'/transactions/{transaction_id}')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        'message': 'Transaction deleted successfully'
    }
