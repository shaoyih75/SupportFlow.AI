import os

from dotenv import load_dotenv

load_dotenv()  # reads backend/.env if present; real environment variables win

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://supportflow:supportflow@localhost:5432/supportflow"
)
