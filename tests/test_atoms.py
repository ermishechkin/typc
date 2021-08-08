from __future__ import annotations

from pytest import raises
from typc import Float, Struct, UInt16, clone_type, sizeof, type_name


def test_zero_init() -> None:
    class SomeStruct(Struct):
        field: UInt16

    assert SomeStruct.field is UInt16


def test_init_zero() -> None:
    class SomeStruct(Struct):
        field: Float

    data = SomeStruct()
    data.field = Float(0)
    assert isinstance(data.field, float)
    assert data.field == 0.0


def test_init_bytes() -> None:
    class SomeStruct(Struct):
        field: UInt16

    data = SomeStruct()
    data.field = UInt16(b'\x12\x34')
    assert data.field == 0x3412


def test_init_native_value() -> None:
    class SomeStruct(Struct):
        field: UInt16

    data = SomeStruct()
    data.field = UInt16(0x1234)
    assert data.field == 0x1234


def test_init_another() -> None:
    class SomeStruct(Struct):
        field: UInt16

    data = SomeStruct()
    data.field = UInt16(UInt16(0x1234))
    assert data.field == 0x1234


def test_init_bad_type() -> None:
    class SomeStruct(Struct):
        field: UInt16

    data = SomeStruct()
    with raises(TypeError):
        data.field = UInt16('bad value')  # type: ignore


def test_type_sizeof() -> None:
    class SomeStruct(Struct):
        field: UInt16

    assert sizeof(SomeStruct.field) == 2


def test_name() -> None:
    class SomeStruct(Struct):
        field: UInt16

    assert type_name(SomeStruct.field) == 'uint16_t'


def test_clone() -> None:
    clone = clone_type(Float)
    data = clone(0)
    assert clone is not Float
    assert sizeof(clone) == 4
    assert type_name(clone) == 'float'
    assert isinstance(data, float)
    assert data == 0.0

    clone2 = clone_type(clone, name='Float')
    assert type_name(clone2) == 'Float'

    clone3 = clone_type(clone2)
    assert type_name(clone3) == 'Float'
