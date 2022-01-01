from __future__ import annotations

from .atom import Integer, Real


class UInt8(Integer):
    __typc_spec__ = 'B'
    __typc_size__ = 1
    __typc_native__ = int
    __typc_name__ = 'uint8_t'


class UInt16(Integer):
    __typc_spec__ = 'H'
    __typc_size__ = 2
    __typc_native__ = int
    __typc_name__ = 'uint16_t'


class UInt32(Integer):
    __typc_spec__ = 'I'
    __typc_size__ = 4
    __typc_native__ = int
    __typc_name__ = 'uint32_t'


class UInt64(Integer):
    __typc_spec__ = 'Q'
    __typc_size__ = 8
    __typc_native__ = int
    __typc_name__ = 'uint64_t'


class Int8(Integer):
    __typc_spec__ = 'b'
    __typc_size__ = 1
    __typc_native__ = int
    __typc_name__ = 'int8_t'


class Int16(Integer):
    __typc_spec__ = 'h'
    __typc_size__ = 2
    __typc_native__ = int
    __typc_name__ = 'int16_t'


class Int32(Integer):
    __typc_spec__ = 'i'
    __typc_size__ = 4
    __typc_native__ = int
    __typc_name__ = 'int32_t'


class Int64(Integer):
    __typc_spec__ = 'q'
    __typc_size__ = 8
    __typc_native__ = int
    __typc_name__ = 'int64_t'


class Float(Real):
    __typc_spec__ = 'f'
    __typc_size__ = 4
    __typc_native__ = float
    __typc_name__ = 'float'


class Double(Real):
    __typc_spec__ = 'd'
    __typc_size__ = 8
    __typc_native__ = float
    __typc_name__ = 'double'
