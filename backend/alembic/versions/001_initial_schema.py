"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2025-11-17

This is a placeholder migration file.
To generate the actual migration based on your models, run:

    alembic revision --autogenerate -m "Initial schema"

This will create a new migration file with all table definitions
from your SQLAlchemy models.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Apply migration changes.

    NOTE: This is a placeholder. Run the following command to generate
    the actual migration:

        alembic revision --autogenerate -m "Initial schema"

    The autogenerate command will create table definitions for:
    - tenants
    - users
    - business_configs
    - services
    - customers
    - appointments
    - conversations

    And PostgreSQL enums:
    - tenant_plan
    - user_role
    - appointment_status
    - cancelled_by
    - message_direction
    - message_type
    """

    # Create PostgreSQL enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE tenant_plan AS ENUM ('free', 'basic', 'premium', 'enterprise');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE user_role AS ENUM ('super_admin', 'admin', 'operator', 'viewer');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE appointment_status AS ENUM ('pending', 'confirmed', 'cancelled', 'completed', 'no_show');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE cancelled_by AS ENUM ('customer', 'business', 'system');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE message_direction AS ENUM ('inbound', 'outbound');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE message_type AS ENUM ('text', 'image', 'audio', 'document', 'location', 'video', 'sticker', 'contact');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # The rest of the table creation will be added by autogenerate
    # When you run: alembic revision --autogenerate -m "Initial schema"
    # Alembic will detect your models and create the appropriate CREATE TABLE statements

    pass


def downgrade() -> None:
    """
    Revert migration changes.

    NOTE: This only drops enums. To properly downgrade including tables,
    you need to generate the full migration with:
        alembic revision --autogenerate -m "Initial schema"
    """

    # Drop enums only (tables should be dropped by subsequent migrations)
    op.execute("DROP TYPE IF EXISTS message_type")
    op.execute("DROP TYPE IF EXISTS message_direction")
    op.execute("DROP TYPE IF EXISTS cancelled_by")
    op.execute("DROP TYPE IF EXISTS appointment_status")
    op.execute("DROP TYPE IF EXISTS user_role")
    op.execute("DROP TYPE IF EXISTS tenant_plan")
