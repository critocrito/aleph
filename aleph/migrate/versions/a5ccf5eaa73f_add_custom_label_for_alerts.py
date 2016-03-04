"""add custom label for alerts

Revision ID: a5ccf5eaa73f
Revises: 670af22aca83
Create Date: 2016-03-04 12:20:53.593011

"""

# revision identifiers, used by Alembic.
revision = 'a5ccf5eaa73f'
down_revision = '670af22aca83'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('alert', sa.Column('custom_label', sa.Unicode(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('alert', 'custom_label')
    ### end Alembic commands ###
