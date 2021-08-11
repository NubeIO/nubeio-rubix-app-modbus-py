import enum


class ModbusType(enum.Enum):
    RTU = 0
    TCP = 1


# The type of checksum to use to verify data integrity. This can be on of the followings.
class ModbusRtuParity(enum.Enum):
    O = 0
    E = 1
    N = 2
    Odd = 3
    Even = 4
