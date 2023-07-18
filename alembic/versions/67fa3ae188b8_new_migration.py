"""New Migration

Revision ID: 67fa3ae188b8
Revises: 194bd6dfaab0
Create Date: 2023-07-17 17:28:39.930624

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '67fa3ae188b8'
down_revision = '194bd6dfaab0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'file_name_and_uuid', ['file_name'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'file_name_and_uuid', type_='unique')
    # ### end Alembic commands ###
