import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
