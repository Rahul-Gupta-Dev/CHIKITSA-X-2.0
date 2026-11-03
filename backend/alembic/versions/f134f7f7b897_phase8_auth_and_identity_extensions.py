"""phase8_auth_and_identity_extensions

Revision ID: f134f7f7b897
Revises: d7c8cd338e97
Create Date: 2026-11-03 14:03:59.107375

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f134f7f7b897'
down_revision: Union[str, Sequence[str], None] = 'd7c8cd338e97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Extend users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('public_id', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('account_status', sa.String(length=32), nullable=True, server_default='PENDING_APPROVAL'))
        batch_op.add_column(sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')))
        batch_op.add_column(sa.Column('phone_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')))
        batch_op.add_column(sa.Column('approval_status', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('approved_by', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('approved_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('rejection_reason', sa.String(length=256), nullable=True))
        batch_op.create_index('ix_users_public_id', ['public_id'], unique=True)
        batch_op.create_index('ix_users_account_status', ['account_status'], unique=False)

    # 2. Extend doctors table
    with op.batch_alter_table('doctors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('medical_registration_number', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('verification_status', sa.String(length=32), nullable=True, server_default='VERIFIED'))
        batch_op.create_index('ix_doctors_user_id', ['user_id'], unique=True)
        batch_op.create_foreign_key(
            'fk_doctors_user_id_users',
            'users',
            ['user_id'], ['id'],
            ondelete='SET NULL'
        )

    # 3. Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('user_id', sa.String(length=64), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(length=128), nullable=False, unique=True),
        sa.Column('family_id', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('replaced_by', sa.String(length=64), nullable=True)
    )
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('ix_refresh_tokens_token_hash', 'refresh_tokens', ['token_hash'], unique=True)
    op.create_index('ix_refresh_tokens_family_id', 'refresh_tokens', ['family_id'])
    op.create_index('ix_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'])

    # 4. Create password_reset_tokens table
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('user_id', sa.String(length=64), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(length=128), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )
    op.create_index('ix_password_reset_tokens_user_id', 'password_reset_tokens', ['user_id'])
    op.create_index('ix_password_reset_tokens_token_hash', 'password_reset_tokens', ['token_hash'], unique=True)
    op.create_index('ix_password_reset_tokens_expires_at', 'password_reset_tokens', ['expires_at'])

    # 5. Create hospital_invitations table
    op.create_table(
        'hospital_invitations',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('hospital_id', sa.String(length=64), sa.ForeignKey('hospitals.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(length=64), unique=True, nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('email', sa.String(length=128), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('used_by_user_id', sa.String(length=64), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=64), nullable=True)
    )
    op.create_index('ix_hospital_invitations_hospital_id', 'hospital_invitations', ['hospital_id'])
    op.create_index('ix_hospital_invitations_code', 'hospital_invitations', ['code'], unique=True)

    # 6. Create auth_audit_logs table
    op.create_table(
        'auth_audit_logs',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('user_id', sa.String(length=64), nullable=True),
        sa.Column('identifier', sa.String(length=128), nullable=False),
        sa.Column('event', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('ip_address', sa.String(length=64), nullable=True),
        sa.Column('user_agent', sa.String(length=256), nullable=True),
        sa.Column('details', sa.String(length=512), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False)
    )
    op.create_index('ix_auth_audit_logs_user_id', 'auth_audit_logs', ['user_id'])
    op.create_index('ix_auth_audit_logs_event', 'auth_audit_logs', ['event'])
    op.create_index('ix_auth_audit_logs_timestamp', 'auth_audit_logs', ['timestamp'])


def downgrade() -> None:
    # 1. Drop new tables
    op.drop_table('auth_audit_logs')
    op.drop_table('hospital_invitations')
    op.drop_table('password_reset_tokens')
    op.drop_table('refresh_tokens')

    # 2. Downgrade doctors table
    with op.batch_alter_table('doctors', schema=None) as batch_op:
        batch_op.drop_constraint('fk_doctors_user_id_users', type_='foreignkey')
        batch_op.drop_index('ix_doctors_user_id')
        batch_op.drop_column('verification_status')
        batch_op.drop_column('medical_registration_number')
        batch_op.drop_column('user_id')

    # 3. Downgrade users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('ix_users_account_status')
        batch_op.drop_index('ix_users_public_id')
        batch_op.drop_column('rejection_reason')
        batch_op.drop_column('approved_at')
        batch_op.drop_column('approved_by')
        batch_op.drop_column('approval_status')
        batch_op.drop_column('phone_verified')
        batch_op.drop_column('email_verified')
        batch_op.drop_column('account_status')
        batch_op.drop_column('public_id')
