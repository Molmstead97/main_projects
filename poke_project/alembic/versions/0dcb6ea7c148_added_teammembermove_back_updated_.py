"""added TeamMemberMove back, updated TeamMember

Revision ID: 0dcb6ea7c148
Revises: 0ad6f2aeb083
Create Date: 2024-08-13 11:43:54.088721

"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '0dcb6ea7c148'
down_revision: str | None = '0ad6f2aeb083'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('team_member_moves',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('team_member_id', sa.Integer(), nullable=False),
    sa.Column('move_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.ForeignKeyConstraint(['move_name'], ['moves.name'], ),
    sa.ForeignKeyConstraint(['team_member_id'], ['team_members.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('team_member_moves')
    # ### end Alembic commands ###
