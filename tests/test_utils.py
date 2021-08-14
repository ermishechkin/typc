from __future__ import annotations

from pytest import raises
from typc import (Struct, UInt8, UInt16, clone_type, offsetof, rename, sizeof,
                  type_name, typeof)


def test_sizeof_type() -> None:
    class SomeStruct(Struct):
        field1: UInt8
        field2: UInt16

    assert sizeof(SomeStruct) == 3


def test_sizeof_value() -> None:
    class SomeStruct(Struct):
        field1: UInt8
        field2: UInt16

    inst = SomeStruct(0)
    assert sizeof(inst) == 3


def test_sizeof_bad() -> None:
    with raises(TypeError):
        _ = sizeof('Invalid value')  # type: ignore


def test_typeof_type() -> None:
    class SomeStruct(Struct):
        field1: UInt8
        field2: UInt16

    with raises(TypeError):
        _ = typeof(SomeStruct)  # type: ignore


def test_typeof_value() -> None:
    class SomeStruct(Struct):
        field1: UInt8
        field2: UInt16

    inst = SomeStruct(0)
    assert typeof(inst) is SomeStruct


def test_typeof_bad() -> None:
    with raises(TypeError):
        _ = typeof('Invalid value')  # type: ignore


def test_offsetof_bad() -> None:
    with raises(TypeError):
        _ = offsetof('Invalid value', 'bad_field')  # type: ignore


def test_type_name_bad() -> None:
    with raises(TypeError):
        _ = type_name('Invalid value')  # type: ignore


def test_clone_bad() -> None:
    with raises(TypeError):
        _ = clone_type('Invalid value')  # type: ignore


def test_clone_bad_name() -> None:
    with raises(TypeError):
        _ = clone_type(UInt16, name=123)  # type: ignore


def test_rename() -> None:
    class SomeStruct(Struct):
        field: UInt8

    rename(SomeStruct, 'AnotherName')
    assert type_name(SomeStruct) == 'AnotherName'


def test_rename_bad() -> None:
    with raises(TypeError):
        rename('Invalid value', 'bad_t')  # type: ignore


def test_rename_bad_name() -> None:
    class SomeStruct(Struct):
        field: UInt8

    with raises(TypeError):
        rename(SomeStruct, name=123)  # type: ignore
