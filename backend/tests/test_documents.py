"""Lesson 7: document upload with S3 presigned POST.

These tests use the real local S3 from docker compose (bucket supportflow-documents-test):
the test client plays the browser, uploading bytes to S3 directly with the presigned POST.
"""

from datetime import timedelta

import httpx
import pytest
from sqlalchemy import func, select

from app.config import MAX_UPLOAD_BYTES, S3_ENDPOINT_URL
from app.db.base import utcnow
from app.deps import get_storage
from app.models import Document
from app.seed import ACME_WS_ID, BOB_WS_ID

HANDBOOK = b"Refunds are processed within 5 business days.\n"
TINY_PDF = b"%PDF-1.4\n1 0 obj << >> endobj\ntrailer << >>\n%%EOF\n"


def docs_url(ws, *parts):
    return "/".join([f"/api/workspaces/{ws}/documents", *[str(p) for p in parts]])


def init(client, headers, *, ws=ACME_WS_ID, filename="handbook.txt", content_type="text/plain", size=len(HANDBOOK)):
    return client.post(
        docs_url(ws, "upload-init"),
        json={"filename": filename, "content_type": content_type, "size_bytes": size},
        headers=headers,
    )


def upload_to_s3(init_body, data, content_type="text/plain"):
    """What the browser does: POST the signed fields + the file straight to S3 (not to our API)."""
    upload = init_body["upload"]
    return httpx.post(upload["url"], data=upload["fields"], files={"file": ("upload", data, content_type)})


def complete(client, headers, document_id, ws=ACME_WS_ID):
    return client.post(docs_url(ws, document_id, "upload-complete"), headers=headers)


def stored(session, document_id) -> Document:
    session.expire_all()
    return session.get(Document, document_id)


# ---------- Completion check (doc order) ----------

@pytest.mark.parametrize(
    "filename, content_type, data",
    [("handbook.txt", "text/plain", HANDBOOK), ("faq.md", "text/markdown", b"# FAQ\n"), ("manual.pdf", "application/pdf", TINY_PDF)],
)
def test_upload_end_to_end_pending_then_uploaded(client, alice, session, filename, content_type, data):
    started = init(client, alice, filename=filename, content_type=content_type, size=len(data))
    assert started.status_code == 201, started.text
    body = started.json()
    doc_id = body["document"]["id"]
    assert body["document"]["status"] == "PENDING"
    assert "storage_key" not in body["document"]  # internal detail, never exposed

    # The PENDING row exists before any byte is uploaded; the key is server-chosen, not the filename.
    row = stored(session, doc_id)
    assert row.status == "PENDING"
    assert row.storage_key == f"workspaces/{ACME_WS_ID}/documents/{doc_id}{filename[filename.rfind('.'):]}"

    sent = upload_to_s3(body, data, content_type)
    assert sent.status_code == 204, sent.text
    assert get_storage().head(row.storage_key).size_bytes == len(data)  # the file really is in S3

    done = complete(client, alice, doc_id)
    assert done.status_code == 200, done.text
    assert done.json()["status"] == "UPLOADED"
    assert done.json()["uploaded_at"] is not None
    assert client.get(docs_url(ACME_WS_ID, doc_id), headers=alice).json()["status"] == "UPLOADED"


def test_complete_is_idempotent_and_never_duplicates(client, alice, session):
    body = init(client, alice).json()
    upload_to_s3(body, HANDBOOK)
    first = complete(client, alice, body["document"]["id"])
    second = complete(client, alice, body["document"]["id"])  # e.g. the first response was lost
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert session.scalar(select(func.count()).select_from(Document)) == 1


def test_file_bytes_go_to_s3_not_through_the_api(client, alice):
    upload = init(client, alice).json()["upload"]
    assert upload["url"].startswith(S3_ENDPOINT_URL)  # the browser POSTs here, not to FastAPI
    assert {"key", "policy", "x-amz-signature", "Content-Type"} <= upload["fields"].keys()


# ---------- failure cases ----------

def test_complete_before_upload_is_a_retryable_409(client, alice, session):
    body = init(client, alice).json()
    doc_id = body["document"]["id"]

    early = complete(client, alice, doc_id)
    assert early.status_code == 409
    assert early.json()["error"]["code"] == "UPLOAD_NOT_FOUND"
    assert stored(session, doc_id).status == "PENDING"

    upload_to_s3(body, HANDBOOK)  # retry after the upload succeeds
    assert complete(client, alice, doc_id).json()["status"] == "UPLOADED"


@pytest.mark.parametrize(
    "filename, content_type",
    [
        ("virus.exe", "application/octet-stream"),
        ("notes.txt", "application/pdf"),  # extension and type disagree
        ("report.pdf", "text/plain"),
        ("README", "text/plain"),  # no extension
    ],
)
def test_unsupported_file_types_are_rejected_before_any_upload(client, alice, session, filename, content_type):
    response = init(client, alice, filename=filename, content_type=content_type)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"
    assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_declared_size_over_10_mib_is_rejected(client, alice):
    response = init(client, alice, size=MAX_UPLOAD_BYTES + 1)
    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "size_bytes"


def test_s3_itself_refuses_a_file_over_the_limit(client, alice):
    body = init(client, alice, size=100).json()  # lies: claims 100 bytes
    sent = upload_to_s3(body, b"x" * (MAX_UPLOAD_BYTES + 1))
    assert sent.status_code == 400
    assert "EntityTooLarge" in sent.text  # stopped by the signed policy, our server never saw it


def test_s3_refuses_a_different_content_type_than_signed(client, alice):
    body = init(client, alice).json()
    fields = {**body["upload"]["fields"], "Content-Type": "application/pdf"}
    sent = httpx.post(body["upload"]["url"], data=fields, files={"file": ("x", HANDBOOK, "application/pdf")})
    assert sent.status_code == 403


def test_size_mismatch_is_rejected_and_the_object_deleted(client, alice, session):
    body = init(client, alice, size=10).json()  # claims 10 bytes, sends more
    doc_id = body["document"]["id"]
    upload_to_s3(body, HANDBOOK)

    response = complete(client, alice, doc_id)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UPLOAD_REJECTED"
    row = stored(session, doc_id)
    assert row.status == "PENDING"
    assert get_storage().head(row.storage_key) is None  # we don't keep bytes we refused


def test_a_text_file_renamed_to_pdf_is_rejected(client, alice):
    body = init(client, alice, filename="fake.pdf", content_type="application/pdf").json()
    upload_to_s3(body, HANDBOOK, "application/pdf")
    response = complete(client, alice, body["document"]["id"])
    assert response.status_code == 400
    assert response.json()["error"]["message"] == "File is not a valid PDF"


def test_upload_never_sent_before_expiry_becomes_expired(client, alice, session):
    doc_id = init(client, alice).json()["document"]["id"]
    row = stored(session, doc_id)
    row.upload_expires_at = utcnow() - timedelta(seconds=1)  # pretend the 5 minutes have passed
    session.commit()

    response = complete(client, alice, doc_id)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "UPLOAD_EXPIRED"
    assert stored(session, doc_id).status == "EXPIRED"


def test_filename_is_display_only_and_cannot_choose_the_path(client, alice, session):
    body = init(client, alice, filename="../../etc/passwd.txt").json()
    assert body["document"]["filename"] == "passwd.txt"
    assert stored(session, body["document"]["id"]).storage_key.startswith(f"workspaces/{ACME_WS_ID}/documents/")


# ---------- permissions (Lesson 6 rules apply to documents too) ----------

def test_viewer_can_read_documents_but_not_upload(client, alice, carol):
    body = init(client, alice).json()
    assert init(client, carol).status_code == 403
    assert complete(client, carol, body["document"]["id"]).status_code == 403
    assert client.get(docs_url(ACME_WS_ID), headers=carol).status_code == 200
    assert client.get(docs_url(ACME_WS_ID, body["document"]["id"]), headers=carol).status_code == 200


def test_member_can_upload(client, bob):
    assert init(client, bob).status_code == 201


def test_cannot_upload_into_someone_elses_workspace(client, alice):
    # The workspace comes from the URL and goes through the membership check: Alice is not in Bob's.
    assert init(client, alice, ws=BOB_WS_ID).status_code == 403


def test_bobs_document_id_under_alices_workspace_is_404(client, alice, bob):
    bobs = init(client, bob, ws=BOB_WS_ID).json()["document"]["id"]
    for method, path in [("get", (bobs,)), ("post", (bobs, "upload-complete")), ("get", (bobs, "download-url"))]:
        response = client.request(method, docs_url(ACME_WS_ID, *path), headers=alice)
        assert response.status_code == 404, path
        assert response.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_list_only_shows_this_workspaces_documents(client, alice, bob):
    init(client, bob, ws=BOB_WS_ID)
    mine = init(client, alice).json()["document"]["id"]
    listed = client.get(docs_url(ACME_WS_ID), headers=alice).json()
    assert [d["id"] for d in listed] == [mine]


# ---------- download ----------

def test_download_url_serves_the_file_from_s3_only_after_upload(client, alice):
    body = init(client, alice).json()
    doc_id = body["document"]["id"]
    assert client.get(docs_url(ACME_WS_ID, doc_id, "download-url"), headers=alice).status_code == 409

    upload_to_s3(body, HANDBOOK)
    complete(client, alice, doc_id)
    link = client.get(docs_url(ACME_WS_ID, doc_id, "download-url"), headers=alice).json()["url"]
    downloaded = httpx.get(link)
    assert downloaded.status_code == 200
    assert downloaded.content == HANDBOOK
    assert "handbook.txt" in downloaded.headers["content-disposition"]
