from alembic import op
import sqlalchemy as sa

revision = 'cbcff6a9de1b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('subscription_status', sa.String(50), nullable=False, server_default='FREE'),
        sa.Column('subscription_plan', sa.String(50), nullable=False, server_default='FREE'),
        sa.Column('subscription_ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'])

    op.create_table('contacts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(30), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_contacts_id', 'contacts', ['id'])
    op.create_index('ix_contacts_email', 'contacts', ['email'])
    op.create_index('ix_contacts_user_id', 'contacts', ['user_id'])

    op.create_table('campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('subject', sa.String(255), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='DRAFT'),
        sa.Column('channel', sa.String(50), nullable=False, server_default='EMAIL'),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_campaigns_id', 'campaigns', ['id'])
    op.create_index('ix_campaigns_user_id', 'campaigns', ['user_id'])
    op.create_index('ix_campaigns_status', 'campaigns', ['status'])

    op.create_table('messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(255), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='PENDING'),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('clicked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('bounced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_messages_id', 'messages', ['id'])
    op.create_index('ix_messages_campaign_id', 'messages', ['campaign_id'])
    op.create_index('ix_messages_contact_id', 'messages', ['contact_id'])
    op.create_index('ix_messages_status', 'messages', ['status'])

    op.create_table('payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('status', sa.String(50), nullable=False, server_default='PENDING'),
        sa.Column('provider', sa.String(50), nullable=False, server_default='STRIPE'),
        sa.Column('provider_ref', sa.String(255), nullable=True),
        sa.Column('provider_metadata', sa.String(1000), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('refunded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_ref')
    )
    op.create_index('ix_payments_id', 'payments', ['id'])
    op.create_index('ix_payments_user_id', 'payments', ['user_id'])
    op.create_index('ix_payments_status', 'payments', ['status'])


def downgrade() -> None:
    op.drop_table('payments')
    op.drop_table('messages')
    op.drop_table('campaigns')
    op.drop_table('contacts')
    op.drop_table('users')