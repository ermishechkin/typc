from __future__ import annotations

from pytest import raises
from typc import Float, Struct, UInt16, sizeof


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
