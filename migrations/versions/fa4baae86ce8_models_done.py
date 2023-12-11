"""models done

Revision ID: fa4baae86ce8
Revises: 1519fbe8a333
Create Date: 2023-12-11 22:56:49.842833

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa4baae86ce8'
down_revision: Union[str, None] = '1519fbe8a333'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
