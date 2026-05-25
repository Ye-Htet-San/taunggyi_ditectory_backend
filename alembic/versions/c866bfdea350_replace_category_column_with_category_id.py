"""Replace category column with category_id

Revision ID: c866bfdea350
Revises: 614a73d7301e
Create Date: 2025-08-30 19:57:04.258976

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c866bfdea350'
down_revision: Union[str, Sequence[str], None] = '614a73d7301e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
     # 1. Create categories table if it doesn't exist
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('name', sa.String, unique=True, nullable=False),
        sa.Column('description', sa.String, default=""),
        sa.Column('icon_url', sa.String, default=""),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True)
    )

    # 2. Rename old places table to temp
    with op.batch_alter_table('places', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category_id', sa.Integer, nullable=True))
        batch_op.create_foreign_key(
            'fk_places_category', 'categories', ['category_id'], ['id']
        )
        batch_op.drop_column('category')

def downgrade() -> None:
    with op.batch_alter_table('places', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category', sa.String, nullable=True))
        batch_op.drop_constraint('fk_places_category', type_='foreignkey')
        batch_op.drop_column('category_id')

    op.drop_table('categories')
