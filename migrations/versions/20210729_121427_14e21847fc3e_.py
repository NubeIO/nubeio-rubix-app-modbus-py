"""empty message

Revision ID: 14e21847fc3e
Revises: 0cff86604ac8
Create Date: 2021-07-29 12:14:27.423371

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
from sqlalchemy.orm import Session

revision = '14e21847fc3e'
down_revision = '0cff86604ac8'
branch_labels = None
depends_on = None

session = Session(bind=op.get_bind())
session.execute('PRAGMA foreign_keys = OFF;')
session.commit()

naming_convention = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
}


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # drop and delete GENERIC
    op.drop_table('point_stores_history')
    op.drop_table('schedules')
    op.drop_table('generic_points')
    op.drop_table('generic_devices')
    op.drop_table('generic_networks')

    delete_point_stores = "DELETE FROM point_stores " \
                          "WHERE point_uuid IN (SELECT uuid FROM points WHERE driver='GENERIC')"
    op.execute(delete_point_stores)
    delete_priority_array = "DELETE FROM priority_array " \
                            "WHERE point_uuid IN (SELECT uuid FROM points WHERE driver='GENERIC')"
    op.execute(delete_priority_array)
    delete_generic_points = "DELETE FROM points WHERE driver='GENERIC'"
    op.execute(delete_generic_points)
    delete_generic_devices = "DELETE FROM devices WHERE driver='GENERIC'"
    op.execute(delete_generic_devices)
    delete_generic_devices = "DELETE FROM networks WHERE driver='GENERIC'"
    op.execute(delete_generic_devices)

    # mappings_mp_gbp
    with op.batch_alter_table('mappings_mp_gbp', schema=None, naming_convention=naming_convention) as batch_op:
        batch_op.drop_constraint('fk_mappings_mp_gbp_point_uuid_modbus_points', type_='foreignkey')
        batch_op.create_foreign_key('point_uuid', 'points',
                                    ['point_uuid'], ['uuid'])

    # points
    with op.batch_alter_table('points', schema=None) as batch_op:
        batch_op.add_column(sa.Column('register', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('register_length', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('function_code',
                                      sa.Enum('READ_COILS', 'READ_DISCRETE_INPUTS', 'READ_HOLDING_REGISTERS',
                                              'READ_INPUT_REGISTERS', 'WRITE_COIL', 'WRITE_REGISTER', 'WRITE_COILS',
                                              'WRITE_REGISTERS', name='modbusfunctioncode'), nullable=True))
        batch_op.add_column(sa.Column('data_type',
                                      sa.Enum('RAW', 'INT16', 'UINT16', 'INT32', 'UINT32', 'FLOAT', 'DOUBLE', 'DIGITAL',
                                              name='modbusdatatype'), nullable=True))
        batch_op.add_column(
            sa.Column('data_endian', sa.Enum('LEB_BEW', 'LEB_LEW', 'BEB_LEW', 'BEB_BEW', name='modbusdataendian'),
                      nullable=True))
        batch_op.add_column(sa.Column('write_value_once', sa.Boolean(), nullable=True))
        batch_op.create_unique_constraint('register_function_code_device_uuid',
                                          ['register', 'function_code', 'device_uuid'])
        batch_op.drop_column('history_enable')
        batch_op.drop_column('history_interval')
        batch_op.drop_column('driver')
        batch_op.drop_column('history_type')
    # modbus_points to points
    mp_to_p = 'UPDATE points SET (register,register_length,function_code,data_type,data_endian,' \
              'write_value_once)=(SELECT register,register_length,function_code,data_type,data_endian,' \
              'write_value_once FROM modbus_points WHERE points.uuid = modbus_points.uuid)'
    op.execute(mp_to_p)
    with op.batch_alter_table('points', schema=None) as batch_op:
        batch_op.alter_column('register', existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column('register_length', existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column('function_code',
                              existing_type=sa.Enum('READ_COILS', 'READ_DISCRETE_INPUTS', 'READ_HOLDING_REGISTERS',
                                                    'READ_INPUT_REGISTERS', 'WRITE_COIL', 'WRITE_REGISTER',
                                                    'WRITE_COILS',
                                                    'WRITE_REGISTERS', name='modbusfunctioncode'), nullable=False)
        batch_op.alter_column('data_type',
                              existing_type=sa.Enum('RAW', 'INT16', 'UINT16', 'INT32', 'UINT32', 'FLOAT',
                                                    'DOUBLE',
                                                    'DIGITAL',
                                                    name='modbusdatatype'), nullable=False)
        batch_op.alter_column('data_endian',
                              existing_type=sa.Enum('LEB_BEW', 'LEB_LEW', 'BEB_LEW', 'BEB_BEW',
                                                    name='modbusdataendian'),
                              nullable=False)
        batch_op.alter_column('write_value_once', existing_type=sa.Boolean(), nullable=False)

    # devices
    with op.batch_alter_table('devices', schema=None) as batch_op:
        batch_op.add_column(sa.Column('type', sa.Enum('RTU', 'TCP', name='modbustype'), nullable=True))
        batch_op.add_column(sa.Column('address', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('zero_based', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('ping_point', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('supports_multiple_rw', sa.Boolean(), nullable=True))
        batch_op.create_unique_constraint('address_network_uuid', ['address', 'network_uuid'])
        batch_op.drop_column('history_enable')
        batch_op.drop_column('driver')
    # modbus_devices to devices
    md_to_d = 'UPDATE devices SET (type,address,zero_based,ping_point,supports_multiple_rw)=' \
              '(SELECT type,address,zero_based,ping_point,supports_multiple_rw FROM modbus_devices ' \
              'WHERE devices.uuid = modbus_devices.uuid)'
    op.execute(md_to_d)
    with op.batch_alter_table('devices', schema=None) as batch_op:
        batch_op.alter_column('type', existing_type=sa.Enum('RTU', 'TCP', name='modbustype'), nullable=False)
        batch_op.alter_column('address', existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column('zero_based', existing_type=sa.Boolean(), nullable=False)
        batch_op.alter_column('supports_multiple_rw', existing_type=sa.Boolean(), nullable=False)

    # networks
    with op.batch_alter_table('networks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rtu_port', sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column('rtu_speed', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('rtu_stop_bits', sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column('rtu_parity', sa.Enum('O', 'E', 'N', 'Odd', 'Even', name='modbusrtuparity'), nullable=True))
        batch_op.add_column(sa.Column('rtu_byte_size', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('tcp_ip', sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column('tcp_port', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('type', sa.Enum('RTU', 'TCP', name='modbustype'), nullable=True))
        batch_op.add_column(sa.Column('timeout', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('polling_interval_runtime', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('point_interval_ms_between_points', sa.Integer(), nullable=True))
        batch_op.create_unique_constraint('rtu_port', ['rtu_port'])
        batch_op.create_unique_constraint('tcp_ip_tcp_port', ['tcp_ip', 'tcp_port'])
        batch_op.drop_column('history_enable')
        batch_op.drop_column('driver')
    # modbus_networks to networks
    mn_to_n = 'UPDATE networks SET (rtu_port,rtu_speed,rtu_stop_bits,rtu_parity,rtu_byte_size,tcp_ip,tcp_port,' \
              'type,timeout,polling_interval_runtime,point_interval_ms_between_points,rtu_port)' \
              '=(SELECT rtu_port,rtu_speed,rtu_stop_bits,rtu_parity,rtu_byte_size,tcp_ip,tcp_port,' \
              'type,timeout,polling_interval_runtime,point_interval_ms_between_points,rtu_port ' \
              'FROM modbus_networks WHERE networks.uuid = modbus_networks.uuid)'
    op.execute(mn_to_n)
    with op.batch_alter_table('networks', schema=None) as batch_op:
        batch_op.alter_column('type', existing_type=sa.Enum('RTU', 'TCP', name='modbustype'), nullable=False)
        batch_op.alter_column('timeout', existing_type=sa.Integer(), nullable=False)

    # drop modbus
    op.drop_table('modbus_networks')
    op.drop_table('modbus_devices')
    op.drop_table('modbus_points')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
