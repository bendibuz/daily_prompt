from firebase_admin import firestore, auth, initialize_app, credentials
from app.models.models import User
from app.adapters.firebase_client import get_firebase_client

get_firebase_client()
db = firestore.client()

def create_user(user: User):
    # TODO: validate user phone number here?
    # TODO: validate any other user info here
    doc_ref = db.collection('users').document(user.phone_number)
    doc_ref.set(user)
    pass

def create_user_v2(user: User):
    try:
        user = auth.create_user(
            email=user.email,
            password=user.password,
            display_name=user.display_name,
            phone_number=user.phone_number,
            uid=user.phone_number
        )
        print(f'Successfully created new user: {user.uid}')
    except Exception as e:
        print(f'Error creating user: {e}')

def create_goals_entry():
    pass