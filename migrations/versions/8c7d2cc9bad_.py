"""empty message

Revision ID: 8c7d2cc9bad
Revises: 224aa564b58d
Create Date: 2014-06-25 21:52:46.303921

"""

# revision identifiers, used by Alembic.
revision = '8c7d2cc9bad'
down_revision = '224aa564b58d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_table('Location')
    op.drop_table('Street')
    op.drop_table('City')
    op.drop_table('County')
    op.drop_table('Country')


def downgrade():
    pass
