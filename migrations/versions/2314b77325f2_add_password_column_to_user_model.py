"""Add password column to user model

Revision ID: 2314b77325f2
Revises: faaba69cf809
Create Date: 2025-03-31 10:50:56.246239

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2314b77325f2'
down_revision = 'faaba69cf809'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password', sa.String(length=255), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('password')

    # ### end Alembic commands ###
