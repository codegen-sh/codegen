
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    username = Column(String(100))
    is_active = Column(Boolean, default=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # Relationships
    organization = relationship("Organization", back_populates="users")
    transactions = relationship("Transaction", back_populates="user")
