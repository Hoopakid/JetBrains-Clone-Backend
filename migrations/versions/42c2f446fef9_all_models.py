"""all models.

Revision ID: 42c2f446fef9
Revises: 
Create Date: 2024-01-21 04:07:46.995086

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42c2f446fef9'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('combo',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('combo_name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('combo_name')
    )
    op.create_table('tools',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tool_name', sa.String(), nullable=True),
    sa.Column('monthly_fee', sa.Float(), nullable=True),
    sa.Column('yearly_fee', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('userdata',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('full_name', sa.String(), nullable=True),
    sa.Column('username', sa.String(), nullable=True),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('balance', sa.Float(), nullable=True),
    sa.Column('password', sa.String(), nullable=True),
    sa.Column('language', sa.Enum('uz', 'eng', 'ru', name='languageenum'), nullable=True),
    sa.Column('birth_date', sa.Date(), nullable=True),
    sa.Column('registered_date', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('combo_products',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('combo_id', sa.Integer(), nullable=True),
    sa.Column('tool_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['combo_id'], ['combo.id'], ),
    sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('coupon',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('coupon', sa.String(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('tool_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
    sa.Column('lifetime', sa.TIMESTAMP(), nullable=True),
    sa.Column('status', sa.Enum('active', 'expired', name='endtimeenum'), nullable=True),
    sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['userdata.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('custom_coupon',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('phone_number', sa.Integer(), nullable=True),
    sa.Column('tool_id', sa.Integer(), nullable=True),
    sa.Column('coupon', sa.String(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
    sa.Column('lifetime', sa.TIMESTAMP(), nullable=True),
    sa.Column('status', sa.Enum('active', 'expired', name='endtimeenum'), nullable=True),
    sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['userdata.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('file',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('file', sa.String(), nullable=True),
    sa.Column('tool_id', sa.Integer(), nullable=True),
    sa.Column('hash', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('hash')
    )
    op.create_table('payment_model',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('tool_id', sa.Integer(), nullable=True),
    sa.Column('lifetime', sa.Enum('month', 'year', name='lifetimeenum'), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
    sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['userdata.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_role',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('role_name', sa.Enum('admin', 'user', name='roleenum'), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['userdata.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_payment',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('payment_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.Enum('delivered', 'processing', 'cancelling', name='status_enum'), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
    sa.ForeignKeyConstraint(['payment_id'], ['payment_model.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['userdata.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_payment')
    op.drop_table('user_role')
    op.drop_table('payment_model')
    op.drop_table('file')
    op.drop_table('custom_coupon')
    op.drop_table('coupon')
    op.drop_table('combo_products')
    op.drop_table('userdata')
    op.drop_table('tools')
    op.drop_table('combo')
    # ### end Alembic commands ###
