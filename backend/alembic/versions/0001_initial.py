"""Initial schema revision — create all tables + vector extension."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # Tables are created via SQLAlchemy metadata in app startup / seed.
    # This revision documents the baseline for environments that use Alembic only.
    bind = op.get_bind()
    from app.core.database import Base
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    from app.core.database import Base
    from app import models  # noqa: F401

    Base.metadata.drop_all(bind=bind)
