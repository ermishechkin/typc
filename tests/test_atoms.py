from __future__ import annotations

from pytest import raises
from typc import (Float, Int16, Struct, UInt8, UInt16, clone_type, sizeof,
                  type_name)


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


def test_eq() -> None:
    assert UInt16 == UInt16  # pylint: disable=comparison-with-itself
    assert UInt16 != UInt8
    assert UInt16 != Int16
    assert UInt16 != Float
    assert UInt16 != int

    clone16 = clone_type(UInt16, name='UInt')
    assert UInt16 == clone16

    clone8 = clone_type(UInt8)
    assert UInt16 != clone8


def test_typechecks_type() -> None:
    clone16 = clone_type(UInt16, name='Word')
    value = clone16(0x1234)

    assert not isinstance(clone16, UInt16)
    assert issubclass(clone16, UInt16)

    assert isinstance(value, UInt16)
    with raises(TypeError):
        issubclass(value, UInt16)  # type: ignore

    assert not isinstance(b'string', UInt16)
    with raises(TypeError):
        issubclass(b'string', UInt16)  # type: ignore


def test_typechecks_type_another() -> None:
    type_w = clone_type(UInt16, name='Word')
    type_f = clone_type(Float, name='Float')
    value_w = type_w(0x1234)

    assert not isinstance(type_w, type_f)
    assert not issubclass(type_w, type_f)

    assert not isinstance(value_w, type_f)
    with raises(TypeError):
        issubclass(value_w, type_f)  # type: ignore
