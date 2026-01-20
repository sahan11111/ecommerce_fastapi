from getpass import getpass

from core.database import SessionLocal
from core.models import User
from core.security import hash_password



def create_superuser():
    db = SessionLocal()

    email = input("Email: ")
    username = input("Username: ")
    password = getpass("Password: ")

    user = User(
        email=email,
        username=username,
        hashed_password=hash_password(password),
        is_superuser=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    print("✅ Superuser created successfully")

if __name__ == "__main__":
    create_superuser()
