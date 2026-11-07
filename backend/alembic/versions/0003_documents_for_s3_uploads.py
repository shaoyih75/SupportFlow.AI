"""documents for s3 uploads

The Lesson 4 `documents` table was a placeholder (title, source_type) with no API writing to it.
It becomes metadata for a file stored in S3: filename, storage_key, content_type, size_bytes,
status PENDING / UPLOADED / EXPIRED.

Autogenerate detected the columns, index, unique and foreign key. Written by hand:
- the two CHECK constraints (autogenerate does NOT detect CHECK changes)
- the downgrade data mapping, so old NOT NULL columns can be restored when rows exist

The new NOT NULL columns are added without defaults: the placeholder table has no rows.
If it somehow does, the upgrade fails loudly instead of inventing data.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-07 00:02:51.781879

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(op.f('ck_documents_source_type_valid'), 'documents', type_='check')
    op.drop_constraint(op.f('ck_documents_status_valid'), 'documents', type_='check')
    op.drop_column('documents', 'title')
    op.drop_column('documents', 'source_type')

    op.add_column('documents', sa.Column('uploaded_by_user_id', sa.Uuid(), nullable=True))
    op.add_column('documents', sa.Column('filename', sa.String(length=255), nullable=False))
    op.add_column('documents', sa.Column('storage_key', sa.String(length=512), nullable=False))
    op.add_column('documents', sa.Column('content_type', sa.String(length=100), nullable=False))
    op.add_column('documents', sa.Column('size_bytes', sa.BigInteger(), nullable=False))
    op.add_column('documents', sa.Column('checksum_sha256', sa.String(length=64), nullable=True))
    op.add_column('documents', sa.Column('upload_expires_at', sa.DateTime(timezone=True), nullable=False))
    op.add_column('documents', sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=True))

    op.create_check_constraint('status_valid', 'documents', "status IN ('PENDING', 'UPLOADED', 'EXPIRED')")
    op.create_check_constraint('size_positive', 'documents', 'size_bytes > 0')
    op.create_unique_constraint(op.f('uq_documents_storage_key'), 'documents', ['storage_key'])
    op.create_foreign_key(
        op.f('fk_documents_uploaded_by_user_id_users'), 'documents', 'users',
        ['uploaded_by_user_id'], ['id'], ondelete='SET NULL',
    )
    op.create_index('ix_documents_workspace_created', 'documents', ['workspace_id', 'created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_documents_workspace_created', table_name='documents')
    op.drop_constraint(op.f('fk_documents_uploaded_by_user_id_users'), 'documents', type_='foreignkey')
    op.drop_constraint(op.f('uq_documents_storage_key'), 'documents', type_='unique')
    op.drop_constraint(op.f('ck_documents_size_positive'), 'documents', type_='check')
    op.drop_constraint(op.f('ck_documents_status_valid'), 'documents', type_='check')

    # Restore the old columns, filling them from the new ones so existing rows stay valid.
    op.add_column('documents', sa.Column('title', sa.String(length=200), nullable=True))
    op.add_column('documents', sa.Column('source_type', sa.String(length=20), nullable=True))
    op.execute(
        """
        UPDATE documents SET
            title = left(filename, 200),
            source_type = CASE WHEN content_type = 'application/pdf' THEN 'pdf' ELSE 'markdown' END,
            status = CASE WHEN status = 'UPLOADED' THEN 'UPLOADED' ELSE 'FAILED' END
        """
    )
    op.alter_column('documents', 'title', nullable=False)
    op.alter_column('documents', 'source_type', nullable=False)
    op.create_check_constraint('source_type_valid', 'documents', "source_type IN ('pdf', 'docx', 'markdown', 'url')")
    op.create_check_constraint('status_valid', 'documents', "status IN ('UPLOADED', 'PROCESSING', 'READY', 'FAILED')")

    op.drop_column('documents', 'uploaded_at')
    op.drop_column('documents', 'upload_expires_at')
    op.drop_column('documents', 'checksum_sha256')
    op.drop_column('documents', 'size_bytes')
    op.drop_column('documents', 'content_type')
    op.drop_column('documents', 'storage_key')
    op.drop_column('documents', 'filename')
    op.drop_column('documents', 'uploaded_by_user_id')
