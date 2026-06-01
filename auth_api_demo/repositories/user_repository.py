from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.user_model import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        """
        Retrieves a user by their unique ID.
        """
        stmt = select(User).where(User.id == user_id)
        return self.db.scalar(stmt)

    def get_by_email(self, email: str) -> User | None:
        """
        Retrieves a user by their email address.
        """
        stmt = select(User).where(User.email == email)
        return self.db.scalar(stmt)

    def get_all(self) -> list[User]:
        """
        Retrieves all registered users in the database.
        """
        stmt = select(User)
        return list(self.db.scalars(stmt).all())

    def create(self, email: str, hashed_password: str, role: str) -> User:
        """
        Creates a new user record in the database.
        """
        user = User(email=email, hashed_password=hashed_password, role=role)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
