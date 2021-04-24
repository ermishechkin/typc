# No "from __future__ import annotations" here !!!

from pytest import raises
from typc import Array, Struct, UInt8, UInt16


def test_struct_declaration_annotations() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    class Rect(Struct):
        pos: Pos
        width: UInt8
        height: UInt8

    assert Rect.pos is Pos
    assert Rect.width is UInt8
    assert Rect.height is UInt8


def test_struct_declaration_mixed() -> None:
    with raises(ValueError):

        class Rect(Struct):
            x = UInt16()
            y: UInt16
            width: UInt8
            height = UInt8()

        _ = Rect


def test_struct_declaration_empty() -> None:
    with raises(ValueError):

        class EmptyStruct(Struct):
            pass

        _ = EmptyStruct


def test_struct_declaration_bad_member() -> None:
    with raises(ValueError):

        class BadStruct(Struct):
            field: str

        _ = BadStruct


def test_array_member_annotation() -> None:
    # This array declaration is not valid - function calls are not allowed
    # in annotations. But we support it in runtime.

    class SomeStruct(Struct):
        field2: Array(UInt16, 4)  # type: ignore

    data = SomeStruct()
    assert bytes(data) == b'\x00\x00\x00\x00\x00\x00\x00\x00'
