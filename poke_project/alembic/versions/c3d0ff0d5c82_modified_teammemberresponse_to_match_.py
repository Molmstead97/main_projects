"""modified TeamMemberResponse to match queries

Revision ID: c3d0ff0d5c82
Revises: bc940f9dd531
Create Date: 2024-08-14 08:30:29.285846

"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'c3d0ff0d5c82'
down_revision: str | None = 'bc940f9dd531'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###