"""Add username to User model

Revision ID: 1a1d57090ebe
Revises: 
Create Date: 2024-10-24 12:53:39.825100

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a1d57090ebe'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('username', sa.String(length=100), nullable=False))
        batch_op.alter_column('email',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
        batch_op.alter_column('password',
               existing_type=sa.VARCHAR(length=150),
               nullable=False)
        
        # Gi et navn til constrainten
        batch_op.create_unique_constraint('uq_user_username', ['username'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        # Fjern constrainten ved å bruke samme navn som da den ble opprettet
        batch_op.drop_constraint('uq_user_username', type_='unique')
        
        batch_op.alter_column('password',
               existing_type=sa.VARCHAR(length=150),
               nullable=True)
        batch_op.alter_column('email',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
        batch_op.drop_column('username')

    # ### end Alembic commands ###
