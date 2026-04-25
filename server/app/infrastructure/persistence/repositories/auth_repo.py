from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from  persistence.models.models import User

class AuthRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def get_user_by_email(self, email: str) -> User | None:
        result = self.session.execute(select(User).where(User.email == email))
        return result.scalars().first()
    
    def create_user(self, user_data: User) -> User:
        user = User(**user_data)
        self.session.add(user)
        self.session.flush()
        return user
    
    def get_user_by_id(self, user_id: str) -> User | None:
        result =  self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    def update_user(self, user_id: str, data: dict) -> User:
        self.session.execute(
            update(User).where(User.id == user_id).values(**data)
        )
        self.session.flush()
        result = self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one()
    
    # Delete user and all related data using CASCADE FK constraints
    def delete_user(self, user_id: str) -> None:
        user =  self.get_user_by_id(user_id)
        if user:
            self.session.delete(user)
            self.session.flush()