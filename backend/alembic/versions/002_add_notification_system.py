"""add_notification_system

Adds notification_logs table and notification fields to business_config.

Revision ID: 002_notification_system
Revises: 001
Create Date: 2024-11-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_notification_system'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create notification_logs table
    op.create_table(
        'notification_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('appointment_id', sa.Integer(), nullable=True),
        sa.Column('recipient_type', sa.String(length=20), nullable=False, comment='customer or owner'),
        sa.Column('recipient_phone', sa.String(length=20), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False, comment='confirmation, reminder_24h, reminder_1h, thanks, cancellation'),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='pending', comment='sent, failed, pending'),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_logs_id'), 'notification_logs', ['id'], unique=False)
    op.create_index('ix_notification_logs_tenant_id', 'notification_logs', ['tenant_id'], unique=False)
    op.create_index('ix_notification_logs_appointment_id', 'notification_logs', ['appointment_id'], unique=False)
    op.create_index('ix_notification_logs_status', 'notification_logs', ['status'], unique=False)

    # Add notification fields to business_config table
    op.add_column('business_configs', sa.Column('notify_owner', sa.Boolean(), nullable=False, server_default='false', comment='Se deve notificar o dono do negócio sobre agendamentos'))
    op.add_column('business_configs', sa.Column('owner_phone', sa.String(length=20), nullable=True, comment='Telefone do dono para receber notificações'))
    op.add_column('business_configs', sa.Column('auto_send_reminders', sa.Boolean(), nullable=False, server_default='true', comment='Se deve enviar lembretes automaticamente'))


def downgrade():
    # Remove notification fields from business_config
    op.drop_column('business_configs', 'auto_send_reminders')
    op.drop_column('business_configs', 'owner_phone')
    op.drop_column('business_configs', 'notify_owner')

    # Drop notification_logs table
    op.drop_index('ix_notification_logs_status', table_name='notification_logs')
    op.drop_index('ix_notification_logs_appointment_id', table_name='notification_logs')
    op.drop_index('ix_notification_logs_tenant_id', table_name='notification_logs')
    op.drop_index(op.f('ix_notification_logs_id'), table_name='notification_logs')
    op.drop_table('notification_logs')
