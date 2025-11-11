"""add symbol timestamps

Revision ID: 2025_11_10_0003
Revises: b95cc4f68f6c
Create Date: 2025-11-10 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2025_11_10_0003'
down_revision = 'b95cc4f68f6c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add timestamp columns to symbols table
    op.add_column('symbols', 
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    op.add_column('symbols', 
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Add unique constraint on symbol
    op.create_unique_constraint('uq_symbol_symbol', 'symbols', ['symbol'])
    
    # Make active column NOT NULL with default
    op.alter_column('symbols', 'active',
               existing_type=sa.Boolean(),
               nullable=False,
               server_default=sa.text('true'))


def downgrade() -> None:
    # Remove constraints and columns
    op.drop_constraint('uq_symbol_symbol', 'symbols', type_='unique')
    op.drop_column('symbols', 'updated_at')
    op.drop_column('symbols', 'created_at')
    op.alter_column('symbols', 'active',
               existing_type=sa.Boolean(),
               nullable=True,
               server_default=None)