import os

from dotenv import load_dotenv

load_dotenv()  # reads backend/.env if present; real environment variables win

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://supportflow:supportflow@localhost:5432/supportflow"
)

# JWT signing key. The default is for local development only: anyone who knows it can
# forge tokens, so production must set a long random JWT_SECRET_KEY outside the code.
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-only-insecure-secret-change-me-0123456789")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Class 6 opening demo only: mounts a deliberately insecure ticket endpoint (IDOR).
# Never enable outside a local classroom demo.
ENABLE_IDOR_DEMO = os.environ.get("ENABLE_IDOR_DEMO") == "1"
