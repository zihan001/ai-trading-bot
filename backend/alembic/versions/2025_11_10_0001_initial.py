from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2025_11_10_0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # enums
    order_side = postgresql.ENUM("buy", "sell", name="orderside")
    order_side.create(op.get_bind(), checkfirst=True)

    order_status = postgresql.ENUM("new", "submitted", "filled", "canceled", "rejected", name="orderstatus")
    order_status.create(op.get_bind(), checkfirst=True)

    # tables
    op.create_table(
        "symbols",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_symbols_symbol", "symbols", ["symbol"], unique=True)

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("broker_order_id", sa.String(length=64), nullable=True),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("side", sa.Enum(name="orderside", native_enum=False), nullable=False),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column("limit_price", sa.Numeric(18, 6), nullable=True),
        sa.Column("status", sa.Enum(name="orderstatus", native_enum=False), nullable=False, server_default="new"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_orders_symbol", "orders", ["symbol"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_broker_order_id", "orders", ["broker_order_id"])

def downgrade() -> None:
    op.drop_index("ix_orders_broker_order_id", table_name="orders")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_index("ix_orders_symbol", table_name="orders")
    op.drop_table("orders")

    op.drop_index("ix_symbols_symbol", table_name="symbols")
    op.drop_table("symbols")

    order_status = postgresql.ENUM(name="orderstatus")
    order_status.drop(op.get_bind(), checkfirst=True)

    order_side = postgresql.ENUM(name="orderside")
    order_side.drop(op.get_bind(), checkfirst=True)
