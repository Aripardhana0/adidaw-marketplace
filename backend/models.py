from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship

from database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    price = Column(String) # Storing as string to match "Rp 3.300.000" format easily for now, or use Float/Integer in real app
    category = Column(String, index=True)
    image = Column(String)
    is_new = Column(Boolean, default=False)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="member")
    name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
