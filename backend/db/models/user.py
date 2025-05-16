from sqlalchemy.orm import Mapped, mapped_column
from backend.db.db import Base

class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(nullable=False)
    jwt_token: Mapped[str] = mapped_column(nullable=False)
    elschool_login : Mapped[str] = mapped_column(nullable=False)
    elschool_password : Mapped[str] = mapped_column(nullable=False)
