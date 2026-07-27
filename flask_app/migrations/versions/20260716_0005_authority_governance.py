"""法源同步触发审计与人工复核决策。"""

from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa

revision: str = "20260716_0005"
down_revision: Union[str, None] = "20260716_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if context.is_offline_mode():
        op.execute("ALTER TABLE authority_sync_runs ADD COLUMN IF NOT EXISTS trigger VARCHAR NOT NULL DEFAULT 'manual'")
        op.execute("ALTER TABLE authority_sync_runs ADD COLUMN IF NOT EXISTS requested_by VARCHAR")
        op.execute("""CREATE TABLE IF NOT EXISTS authority_source_reviews (
            id VARCHAR PRIMARY KEY,
            authority_id VARCHAR NOT NULL REFERENCES legal_authorities(id) ON DELETE CASCADE,
            source_snapshot_id VARCHAR REFERENCES authority_source_snapshots(id) ON DELETE SET NULL,
            decision VARCHAR NOT NULL,
            reviewer_id VARCHAR NOT NULL,
            notes TEXT,
            decided_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now())""")
        op.execute("CREATE INDEX IF NOT EXISTS ix_authority_reviews_authority_id ON authority_source_reviews (authority_id)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_authority_reviews_decision ON authority_source_reviews (decision)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_authority_reviews_reviewer_id ON authority_source_reviews (reviewer_id)")
        return

    inspector = sa.inspect(op.get_bind())
    sync_columns = {column["name"] for column in inspector.get_columns("authority_sync_runs")}
    if "trigger" not in sync_columns:
        op.add_column(
            "authority_sync_runs",
            sa.Column("trigger", sa.String(), nullable=False, server_default="manual"),
        )
    if "requested_by" not in sync_columns:
        op.add_column("authority_sync_runs", sa.Column("requested_by", sa.String()))

    if "authority_source_reviews" not in set(inspector.get_table_names()):
        op.create_table(
            "authority_source_reviews",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column(
                "authority_id",
                sa.String(),
                sa.ForeignKey("legal_authorities.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "source_snapshot_id",
                sa.String(),
                sa.ForeignKey("authority_source_snapshots.id", ondelete="SET NULL"),
            ),
            sa.Column("decision", sa.String(), nullable=False),
            sa.Column("reviewer_id", sa.String(), nullable=False),
            sa.Column("notes", sa.Text()),
            sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    inspector = sa.inspect(op.get_bind())
    known = {item["name"] for item in inspector.get_indexes("authority_source_reviews")}
    for name, columns in (
        ("ix_authority_reviews_authority_id", ["authority_id"]),
        ("ix_authority_reviews_decision", ["decision"]),
        ("ix_authority_reviews_reviewer_id", ["reviewer_id"]),
    ):
        if name not in known:
            op.create_index(name, "authority_source_reviews", columns)


def downgrade() -> None:
    op.drop_index("ix_authority_reviews_reviewer_id", table_name="authority_source_reviews")
    op.drop_index("ix_authority_reviews_decision", table_name="authority_source_reviews")
    op.drop_index("ix_authority_reviews_authority_id", table_name="authority_source_reviews")
    op.drop_table("authority_source_reviews")
    op.drop_column("authority_sync_runs", "requested_by")
    op.drop_column("authority_sync_runs", "trigger")
