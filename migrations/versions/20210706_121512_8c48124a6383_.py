"""empty message

Revision ID: 8c48124a6383
Revises: 0b90dc1a4c97
Create Date: 2021-07-06 12:15:12.737360

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c48124a6383'
down_revision = '0b90dc1a4c97'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('mappings_mp_gbp', schema=None) as batch_op:
        batch_op.alter_column('modbus_point_uuid', new_column_name='point_uuid')
        batch_op.alter_column('modbus_point_name', new_column_name='point_name')
        batch_op.alter_column('generic_point_uuid', new_column_name='mapped_point_uuid')
        batch_op.alter_column('generic_point_name', new_column_name='mapped_point_name')
        batch_op.add_column(sa.Column('type', sa.Enum('GENERIC', 'BACNET', name='maptype'), nullable=True))
        batch_op.add_column(
            sa.Column('mapping_state', sa.Enum('MAPPED', 'BROKEN', name='mappingstate'), server_default="MAPPED"))

    # generic to mapped
    transfer_generic = "UPDATE mappings_mp_gbp SET type='GENERIC'"
    op.execute(transfer_generic)

    # bacnet to mapped
    transfer_bacnet = "UPDATE mappings_mp_gbp SET mapped_point_uuid = bacnet_point_uuid, mapped_point_name = " \
                      "bacnet_point_name, type='BACNET' " \
                      "WHERE bacnet_point_uuid IS NOT NULL OR bacnet_point_uuid != ''"
    op.execute(transfer_bacnet)

    with op.batch_alter_table('mappings_mp_gbp', schema=None) as batch_op:
        batch_op.drop_column('bacnet_point_uuid')
        batch_op.drop_column('bacnet_point_name')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('mappings_mp_gbp', schema=None) as batch_op:
        batch_op.alter_column('point_uuid', new_column_name='modbus_point_uuid')
        batch_op.alter_column('point_name', new_column_name='modbus_point_name')
        batch_op.alter_column('mapped_point_uuid', new_column_name='generic_point_uuid')
        batch_op.alter_column('mapped_point_name', new_column_name='generic_point_name')
        batch_op.add_column(sa.Column('bacnet_point_uuid', sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column('bacnet_point_name', sa.String(length=80), nullable=True))
        batch_op.create_unique_constraint("bacnet_point_uuid_constraint", ["bacnet_point_uuid"])

    # mapped to bacnet
    transfer_bacnet = "UPDATE mappings_mp_gbp SET bacnet_point_uuid = generic_point_uuid, bacnet_point_name = " \
                      "generic_point_name, generic_point_uuid = NULL, generic_point_name = NULL " \
                      "WHERE type = 'BACNET'"
    op.execute(transfer_bacnet)

    with op.batch_alter_table('mappings_mp_gbp', schema=None) as batch_op:
        batch_op.drop_column('type')
        batch_op.drop_column('mapping_state')

    # ### end Alembic commands ###
