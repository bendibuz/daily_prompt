from firebase_admin import firestore

from app.models.models import User

db = firestore.client()

def create_user(user: User):
    # TODO: validate user phone number here?
    # TODO: validate any other user info here
    doc_ref = db.collection('users').document(user.phone_number)
    doc_ref.set(user)
    pass

def create_goals_entry():
    pass