"""Lesson 7 demo: upload a file the way any client would, in three steps.

    cd backend
    python scripts/upload_demo.py                      # uploads scripts/handbook.txt as alice
    python scripts/upload_demo.py path/to/manual.pdf   # any .pdf / .txt / .md

Needs the API running (uvicorn app.main:app --reload) and `docker compose up -d --wait`.
"""

import mimetypes
import os
import sys
from pathlib import Path

import httpx

API = os.environ.get("API_URL", "http://localhost:8000/api")
WORKSPACE_ID = "11111111-1111-1111-1111-111111111111"  # Acme Support (seed data)
TYPES = {".pdf": "application/pdf", ".txt": "text/plain", ".md": "text/markdown"}


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("handbook.txt")
    content_type = TYPES.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    data = path.read_bytes()

    token = httpx.post(f"{API}/auth/login", json={"email": "alice@example.com", "password": "password123"})
    token.raise_for_status()
    headers = {"Authorization": f"Bearer {token.json()['access_token']}"}
    docs = f"{API}/workspaces/{WORKSPACE_ID}/documents"

    # Step 1: ask our API for permission. Only metadata is sent here, no file bytes.
    init = httpx.post(
        f"{docs}/upload-init",
        json={"filename": path.name, "content_type": content_type, "size_bytes": len(data)},
        headers=headers,
    )
    init.raise_for_status()
    result = init.json()
    doc_id = result["document"]["id"]
    print(f"1. upload-init     → document {doc_id} is {result['document']['status']}")
    print(f"                     upload goes to {result['upload']['url']} (S3, not our API)")

    # Step 2: send the bytes straight to S3 with the signed form fields.
    sent = httpx.post(result["upload"]["url"], data=result["upload"]["fields"], files={"file": (path.name, data, content_type)})
    sent.raise_for_status()
    print(f"2. POST to S3      → HTTP {sent.status_code}, {len(data)} bytes stored")

    # Step 3: tell our API we're done; it checks S3 itself before believing us.
    done = httpx.post(f"{docs}/{doc_id}/upload-complete", headers=headers)
    done.raise_for_status()
    print(f"3. upload-complete → {done.json()['status']}")

    print()
    print("Check it yourself:")
    print(f'  docker compose exec db psql -U supportflow -c "select filename, storage_key, size_bytes, status from documents where id = \'{doc_id}\';"')
    print("  docker compose exec s3 awslocal s3 ls --recursive s3://supportflow-documents/")


if __name__ == "__main__":
    main()
