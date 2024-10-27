"""Fix recurring_transaction_id ForeignKey in Transaction model

Revision ID: <revision_id>
Revises: <previous_revision_id>
Create Date: 2024-10-27 xx:xx:xx.xxxxxx

"""
from alembic import op
import sqlalchemy as sa

revision = 'e31b8acb9b23'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # Create a new temporary table with the correct ForeignKey
    op.create_table(
        'transaction_new',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=True),
        sa.Column('recurring', sa.Boolean(), nullable=True, default=False),
        sa.Column('recurring_transaction_id', sa.Integer(), sa.ForeignKey('recurring_transaction.id'), nullable=True),
    )

    # Copy data from the old table to the new table
    op.execute("""
        INSERT INTO transaction_new (id, date, category_id, description, amount, type, recurring, recurring_transaction_id)
        SELECT id, date, category_id, description, amount, type, recurring, recurring_transaction_id FROM transaction
    """)

    # Drop the old table
    op.drop_table('transaction')

    # Rename the new table to the original name
    op.rename_table('transaction_new', 'transaction')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # Recreate the old table without the correct ForeignKey
    op.create_table(
        'transaction_old',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=True),
        sa.Column('recurring', sa.Boolean(), nullable=True, default=False),
        sa.Column('recurring_transaction_id', sa.Integer(), sa.ForeignKey('transaction.id'), nullable=True),
    )

    # Copy data from the corrected table to the old table
    op.execute("""
        INSERT INTO transaction_old (id, date, category_id, description, amount, type, recurring, recurring_transaction_id)
        SELECT id, date, category_id, description, amount, type, recurring, recurring_transaction_id FROM transaction
    """)

    # Drop the corrected table
    op.drop_table('transaction')

    # Rename the old table back to the original name
    op.rename_table('transaction_old', 'transaction')
    # ### end Alembic commands ###