from alembic import op
import sqlalchemy as sa


revision = "4f9f5c7b8c2d"
down_revision = "cbcff6a9de1b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organizations_id", "organizations", ["id"])
    op.create_index("ix_organizations_owner_user_id", "organizations", ["owner_user_id"])
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)

    op.create_table(
        "memberships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="member"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_memberships_org_user"),
    )
    op.create_index("ix_memberships_id", "memberships", ["id"])
    op.create_index("ix_memberships_organization_id", "memberships", ["organization_id"])
    op.create_index("ix_memberships_user_id", "memberships", ["user_id"])

    op.add_column("contacts", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.add_column("campaigns", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.add_column("payments", sa.Column("organization_id", sa.Integer(), nullable=True))

    op.create_foreign_key(
        "fk_contacts_organization_id_organizations",
        "contacts",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_campaigns_organization_id_organizations",
        "campaigns",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_payments_organization_id_organizations",
        "payments",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index("ix_contacts_organization_id", "contacts", ["organization_id"])
    op.create_index("ix_campaigns_organization_id", "campaigns", ["organization_id"])
    op.create_index("ix_payments_organization_id", "payments", ["organization_id"])

    op.execute(
        """
        INSERT INTO organizations (name, slug, owner_user_id, created_at, updated_at)
        SELECT
            users.full_name || '''s Workspace',
            'workspace-' || users.id,
            users.id,
            NOW(),
            NOW()
        FROM users
        """
    )

    op.execute(
        """
        INSERT INTO memberships (organization_id, user_id, role, created_at, updated_at)
        SELECT
            organizations.id,
            organizations.owner_user_id,
            'owner',
            NOW(),
            NOW()
        FROM organizations
        """
    )

    op.execute(
        """
        UPDATE contacts
        SET organization_id = organizations.id
        FROM organizations
        WHERE organizations.owner_user_id = contacts.user_id
        """
    )
    op.execute(
        """
        UPDATE campaigns
        SET organization_id = organizations.id
        FROM organizations
        WHERE organizations.owner_user_id = campaigns.user_id
        """
    )
    op.execute(
        """
        UPDATE payments
        SET organization_id = organizations.id
        FROM organizations
        WHERE organizations.owner_user_id = payments.user_id
        """
    )

    op.alter_column("contacts", "organization_id", nullable=False)
    op.alter_column("campaigns", "organization_id", nullable=False)
    op.alter_column("payments", "organization_id", nullable=False)


def downgrade() -> None:
    op.drop_index("ix_payments_organization_id", table_name="payments")
    op.drop_constraint("fk_payments_organization_id_organizations", "payments", type_="foreignkey")
    op.drop_column("payments", "organization_id")

    op.drop_index("ix_campaigns_organization_id", table_name="campaigns")
    op.drop_constraint("fk_campaigns_organization_id_organizations", "campaigns", type_="foreignkey")
    op.drop_column("campaigns", "organization_id")

    op.drop_index("ix_contacts_organization_id", table_name="contacts")
    op.drop_constraint("fk_contacts_organization_id_organizations", "contacts", type_="foreignkey")
    op.drop_column("contacts", "organization_id")

    op.drop_index("ix_memberships_user_id", table_name="memberships")
    op.drop_index("ix_memberships_organization_id", table_name="memberships")
    op.drop_index("ix_memberships_id", table_name="memberships")
    op.drop_table("memberships")

    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_index("ix_organizations_owner_user_id", table_name="organizations")
    op.drop_index("ix_organizations_id", table_name="organizations")
    op.drop_table("organizations")
