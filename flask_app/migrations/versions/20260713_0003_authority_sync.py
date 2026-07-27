"""生产法源快照、同步批次和新鲜度字段。"""

from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa

revision: str = "20260713_0003"
down_revision: Union[str, None] = "20260713_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if context.is_offline_mode():
        op.execute("ALTER TABLE legal_authorities ADD COLUMN IF NOT EXISTS fresh_until TIMESTAMP WITH TIME ZONE")
        op.execute("ALTER TABLE legal_authorities ADD COLUMN IF NOT EXISTS source_snapshot_id VARCHAR")
        op.execute("ALTER TABLE legal_authorities ADD COLUMN IF NOT EXISTS verification_method VARCHAR")
        op.execute("""CREATE TABLE IF NOT EXISTS authority_sync_runs (
            id VARCHAR PRIMARY KEY, provider VARCHAR NOT NULL, status VARCHAR NOT NULL,
            fetched_count INTEGER NOT NULL DEFAULT 0, imported_count INTEGER NOT NULL DEFAULT 0,
            unchanged_count INTEGER NOT NULL DEFAULT 0, review_required_count INTEGER NOT NULL DEFAULT 0,
            error_code VARCHAR, error_message TEXT, started_at TIMESTAMP WITH TIME ZONE NOT NULL,
            completed_at TIMESTAMP WITH TIME ZONE)""")
        op.execute("""CREATE TABLE IF NOT EXISTS authority_source_snapshots (
            id VARCHAR PRIMARY KEY, sync_run_id VARCHAR NOT NULL REFERENCES authority_sync_runs(id) ON DELETE CASCADE,
            authority_id VARCHAR REFERENCES legal_authorities(id) ON DELETE SET NULL,
            provider VARCHAR NOT NULL, external_id VARCHAR NOT NULL, canonical_url TEXT NOT NULL,
            media_type VARCHAR NOT NULL, source_content_hash VARCHAR NOT NULL, raw_content BYTEA NOT NULL,
            etag VARCHAR, last_modified VARCHAR, verification_method VARCHAR NOT NULL,
            verification_status VARCHAR NOT NULL, retrieved_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            CONSTRAINT uq_authority_snapshot_run_source UNIQUE (sync_run_id, external_id))""")
        for statement in (
            "CREATE INDEX IF NOT EXISTS ix_legal_authorities_fresh_until ON legal_authorities (fresh_until)",
            "CREATE INDEX IF NOT EXISTS ix_authority_sync_runs_provider_status ON authority_sync_runs (provider, status)",
            "CREATE INDEX IF NOT EXISTS ix_authority_snapshots_provider_external ON authority_source_snapshots (provider, external_id)",
            "CREATE INDEX IF NOT EXISTS ix_authority_snapshots_retrieved_at ON authority_source_snapshots (retrieved_at)",
        ):
            op.execute(statement)
        return
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    authority_columns = {column["name"] for column in inspector.get_columns("legal_authorities")}
    for name, column in [
        ("fresh_until", sa.Column("fresh_until", sa.DateTime(timezone=True))),
        ("source_snapshot_id", sa.Column("source_snapshot_id", sa.String())),
        ("verification_method", sa.Column("verification_method", sa.String())),
    ]:
        if name not in authority_columns:
            op.add_column("legal_authorities", column)

    if "authority_sync_runs" not in tables:
        op.create_table(
            "authority_sync_runs",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("provider", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("fetched_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("imported_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("unchanged_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("review_required_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("error_code", sa.String()),
            sa.Column("error_message", sa.Text()),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
        )
    if "authority_source_snapshots" not in tables:
        op.create_table(
            "authority_source_snapshots",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("sync_run_id", sa.String(), sa.ForeignKey("authority_sync_runs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("authority_id", sa.String(), sa.ForeignKey("legal_authorities.id", ondelete="SET NULL")),
            sa.Column("provider", sa.String(), nullable=False),
            sa.Column("external_id", sa.String(), nullable=False),
            sa.Column("canonical_url", sa.Text(), nullable=False),
            sa.Column("media_type", sa.String(), nullable=False),
            sa.Column("source_content_hash", sa.String(), nullable=False),
            sa.Column("raw_content", sa.LargeBinary(), nullable=False),
            sa.Column("etag", sa.String()),
            sa.Column("last_modified", sa.String()),
            sa.Column("verification_method", sa.String(), nullable=False),
            sa.Column("verification_status", sa.String(), nullable=False),
            sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("sync_run_id", "external_id", name="uq_authority_snapshot_run_source"),
        )
    inspector = sa.inspect(op.get_bind())
    index_specs = {
        "legal_authorities": [("ix_legal_authorities_fresh_until", ["fresh_until"])],
        "authority_sync_runs": [("ix_authority_sync_runs_provider_status", ["provider", "status"])],
        "authority_source_snapshots": [
            ("ix_authority_snapshots_provider_external", ["provider", "external_id"]),
            ("ix_authority_snapshots_retrieved_at", ["retrieved_at"]),
        ],
    }
    for table, specs in index_specs.items():
        known = {item["name"] for item in inspector.get_indexes(table)}
        for name, columns in specs:
            if name not in known:
                op.create_index(name, table, columns)


def downgrade() -> None:
    op.drop_index("ix_authority_snapshots_retrieved_at", table_name="authority_source_snapshots")
    op.drop_index("ix_authority_snapshots_provider_external", table_name="authority_source_snapshots")
    op.drop_index("ix_authority_sync_runs_provider_status", table_name="authority_sync_runs")
    op.drop_table("authority_source_snapshots")
    op.drop_table("authority_sync_runs")
    op.drop_index("ix_legal_authorities_fresh_until", table_name="legal_authorities")
    for column in ("verification_method", "source_snapshot_id", "fresh_until"):
        op.drop_column("legal_authorities", column)
