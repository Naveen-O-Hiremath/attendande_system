"""Import this module wherever Alembic needs the full model metadata."""

from app.db.base_class import Base
from app.models import *  # noqa: F401,F403
