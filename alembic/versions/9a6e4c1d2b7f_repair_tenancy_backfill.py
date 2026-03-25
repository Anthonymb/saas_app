from alembic import op


revision = "9a6e4c1d2b7f"
down_revision = "4f9f5c7b8c2d"
branch_labels = None
depends_on = None


def upgrade() -> None:
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
        LEFT JOIN organizations
            ON organizations.owner_user_id = users.id
        WHERE organizations.id IS NULL
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
        LEFT JOIN memberships
            ON memberships.organization_id = organizations.id
           AND memberships.user_id = organizations.owner_user_id
        WHERE memberships.id IS NULL
        """
    )

    op.execute(
        """
        UPDATE contacts
        SET organization_id = organizations.id
        FROM organizations
        WHERE contacts.organization_id IS NULL
          AND organizations.owner_user_id = contacts.user_id
        """
    )

    op.execute(
        """
        UPDATE campaigns
        SET organization_id = organizations.id
        FROM organizations
        WHERE campaigns.organization_id IS NULL
          AND organizations.owner_user_id = campaigns.user_id
        """
    )

    op.execute(
        """
        UPDATE payments
        SET organization_id = organizations.id
        FROM organizations
        WHERE payments.organization_id IS NULL
          AND organizations.owner_user_id = payments.user_id
        """
    )


def downgrade() -> None:
    pass
