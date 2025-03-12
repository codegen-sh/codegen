

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from .base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    xero_organization_id = Column(String(50), unique=True)
    stripe_customer_id = Column(String(100))
    updated_at = Column(DateTime)

    # Relationships
    users = relationship("User", back_populates="organization")
    transactions = relationship("Transaction", back_populates="organization")
