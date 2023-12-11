"""models done

Revision ID: d89a3ebccd2f
Revises: fa4baae86ce8
Create Date: 2023-12-11 23:02:36.015045

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd89a3ebccd2f'
down_revision: Union[str, None] = 'fa4baae86ce8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
