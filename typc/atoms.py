from __future__ import annotations

from .atom import AtomType


class UInt8(AtomType[int]):
    __typc_spec__ = 'B'
    __typc_size__ = 1
    __typc_native__ = int


class UInt16(AtomType[int]):
    __typc_spec__ = 'H'
    __typc_size__ = 2
    __typc_native__ = int


class UInt32(AtomType[int]):
    __typc_spec__ = 'I'
    __typc_size__ = 4
    __typc_native__ = int


class UInt64(AtomType[int]):
    __typc_spec__ = 'Q'
    __typc_size__ = 8
    __typc_native__ = int


class Int8(AtomType[int]):
    __typc_spec__ = 'b'
    __typc_size__ = 1
    __typc_native__ = int


class Int16(AtomType[int]):
    __typc_spec__ = 'h'
    __typc_size__ = 2
    __typc_native__ = int


class Int32(AtomType[int]):
    __typc_spec__ = 'i'
    __typc_size__ = 4
    __typc_native__ = int


class Int64(AtomType[int]):
    __typc_spec__ = 'q'
    __typc_size__ = 8
    __typc_native__ = int


class Float(AtomType[float]):
    __typc_spec__ = 'f'
    __typc_size__ = 4
    __typc_native__ = float


class Double(AtomType[float]):
    __typc_spec__ = 'd'
    __typc_size__ = 8
    __typc_native__ = float
