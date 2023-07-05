"""New Migration

Revision ID: 13c17cd1a979
Revises: ce46770d40f0
Create Date: 2023-07-05 16:08:40.179349

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '13c17cd1a979'
down_revision = 'ce46770d40f0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('binary_results', sa.Column('raw_data_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'binary_results', 'raw_data', ['raw_data_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'binary_results', type_='foreignkey')
    op.drop_column('binary_results', 'raw_data_id')
    # ### end Alembic commands ###
