"""New Migration

Revision ID: ce46770d40f0
Revises: a7d8d2671546
Create Date: 2023-07-03 13:16:27.728983

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ce46770d40f0'
down_revision = 'a7d8d2671546'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('file_name_and_uuid',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('file_name', sa.String(), nullable=True),
    sa.Column('file_uuid', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_file_name_and_uuid_id'), 'file_name_and_uuid', ['id'], unique=False)
    op.create_table('binary_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sequence_id', sa.String(), nullable=True),
    sa.Column('type', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('file_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['file_id'], ['file_name_and_uuid.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_binary_results_id'), 'binary_results', ['id'], unique=False)
    op.create_table('raw_data',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sequence_id', sa.String(), nullable=True),
    sa.Column('sequence', sa.String(), nullable=True),
    sa.Column('sequence_length', sa.Integer(), nullable=True),
    sa.Column('min_quality', sa.Integer(), nullable=True),
    sa.Column('max_quality', sa.Integer(), nullable=True),
    sa.Column('average_quality', sa.Float(), nullable=True),
    sa.Column('phred_quality', sa.String(), nullable=True),
    sa.Column('file_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['file_id'], ['file_name_and_uuid.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('sequence_id')
    )
    op.create_index(op.f('ix_raw_data_id'), 'raw_data', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_raw_data_id'), table_name='raw_data')
    op.drop_table('raw_data')
    op.drop_index(op.f('ix_binary_results_id'), table_name='binary_results')
    op.drop_table('binary_results')
    op.drop_index(op.f('ix_file_name_and_uuid_id'), table_name='file_name_and_uuid')
    op.drop_table('file_name_and_uuid')
    # ### end Alembic commands ###