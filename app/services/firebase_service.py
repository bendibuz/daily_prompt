from firebase_admin import firestore, auth

from app.models.models import User

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
            email='newuser@example.com',
            password='strongpassword',
            display_name='New User',
            phone_number=''
            # uid='custom-uid-if-desired' # Optional: provide a custom UID
        )
        print(f'Successfully created new user: {user.uid}')
    except Exception as e:
        print(f'Error creating user: {e}')

def create_goals_entry():
    pass