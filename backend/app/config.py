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

# ---------- S3 (document file storage) ----------
# Defaults point at the local S3 from docker compose. For real AWS: set S3_ENDPOINT_URL to an
# empty value and leave the two keys unset, so boto3 uses your normal AWS credentials (AWS_PROFILE etc.).
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "http://localhost:4566") or None
S3_REGION = os.environ.get("S3_REGION", "us-east-1")
S3_BUCKET = os.environ.get("S3_BUCKET", "supportflow-documents")
S3_ACCESS_KEY_ID = os.environ.get("S3_ACCESS_KEY_ID", "test" if S3_ENDPOINT_URL else "") or None
S3_SECRET_ACCESS_KEY = os.environ.get("S3_SECRET_ACCESS_KEY", "test" if S3_ENDPOINT_URL else "") or None

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MiB: the real file size limit
UPLOAD_URL_EXPIRES_SECONDS = 300  # a presigned upload is valid for 5 minutes
