from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()


def get_db() -> Session:
    # Placeholder for DB session creation
    pass
