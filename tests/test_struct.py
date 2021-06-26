from __future__ import annotations

from typing import Literal
from typing_extensions import Annotated

from pytest import raises
from typc import (Padding, Shift, Struct, UInt8, UInt16, offsetof, padded,
                  shifted, sizeof, typeof)


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


def test_struct_declaration_classvars() -> None:
    class Pos(Struct):
        x = UInt16()
        y = UInt16()

    class Rect(Struct):
        pos = Pos()
        width = UInt8()
        height = UInt8()

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


def test_empty_struct_declaration() -> None:
    with raises(ValueError):

        class EmptyStruct(Struct):
            pass

        _ = EmptyStruct


def test_non_type_field_annotation() -> None:
    with raises(ValueError):

        class BadStruct(Struct):
            field: str

        _ = BadStruct


def test_non_type_field_classvar() -> None:
    with raises(ValueError):

        class BadStruct(Struct):
            field = int

        _ = BadStruct


def test_nonexistent_type_member_get() -> None:
    class SomeStruct(Struct):
        field: UInt8

    with raises(AttributeError):
        # pylint: disable=no-member
        _ = SomeStruct.bad  # type: ignore


def test_nonexistent_type_member_set() -> None:
    class SomeStruct(Struct):
        field: UInt8

    with raises(AttributeError):
        SomeStruct.bad = 1  # type: ignore


def test_nonexistent_value_member_get() -> None:
    class SomeStruct(Struct):
        field: UInt8

    inst = SomeStruct(0)
    with raises(AttributeError):
        # pylint: disable=no-member
        _ = inst.bad  # type: ignore


def test_nonexistent_value_member_set() -> None:
    class SomeStruct(Struct):
        field: UInt8

    inst = SomeStruct(0)
    with raises(AttributeError):
        # pylint: disable=attribute-defined-outside-init
        inst.bad = 1  # type: ignore


def test_packed_size() -> None:
    class SomeStruct(Struct):
        field1: UInt8
        field2: UInt16

    data = SomeStruct(0)
    assert sizeof(SomeStruct) == 3
    assert sizeof(data) == 3
    assert bytes(data) == b'\x00\x00\x00'


def test_typeof() -> None:
    class SomeStruct(Struct):
        field1: UInt8
        field2: UInt16

    data = SomeStruct(0)
    assert typeof(data) is SomeStruct


def test_offsetof_type() -> None:
    class SomeStruct(Struct):
        field1: UInt8
        field2: UInt16
        field3: UInt16

    assert offsetof(SomeStruct, 'field1') == 0
    assert offsetof(SomeStruct, 'field2') == 1
    assert offsetof(SomeStruct, 'field3') == 3
    with raises(KeyError):
        offsetof(SomeStruct, 'bad_field')


def test_offsetof_value() -> None:
    class SomeStruct(Struct):
        field1: UInt8
        field2: UInt16
        field3: UInt16

    data = SomeStruct(0)
    assert offsetof(data, 'field1') == 0
    assert offsetof(data, 'field2') == 1
    assert offsetof(data, 'field3') == 3
    with raises(KeyError):
        offsetof(data, 'bad_field')


def test_init_zero() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    class Size(Struct):
        width: UInt8
        height: UInt8

    class Rect(Struct):
        pos: Pos
        size: Size

    rect = Rect(0)
    assert rect.pos.x == 0
    assert rect.pos.y == 0
    assert rect.size.height == 0
    assert rect.size.width == 0

    assert bytes(rect) == b'\x00\x00\x00\x00\x00\x00'


def test_init_tuple() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    pos = Pos((1, 2))
    assert pos.x == 1
    assert pos.y == 2


def test_init_bytes() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    pos = Pos(b'\x11\x22\x33\x44')
    assert pos.x == 0x2211
    assert pos.y == 0x4433


def test_init_struct() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    pos = Pos(Pos((0x1122, 0x3344)))
    assert pos.x == 0x1122
    assert pos.y == 0x3344


def test_init_bad_type() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    with raises(TypeError):
        Pos('bad value')  # type: ignore


def test_unitialized_member_access() -> None:
    class SomeStruct(Struct):
        field1: UInt16
        field2: UInt16

    inst = SomeStruct()
    assert inst.field2 == 0


def test_unitialized_member_assignment() -> None:
    class SomeStruct(Struct):
        field1: UInt16
        field2: UInt16

    inst = SomeStruct()
    inst.field2 = 0x1122
    assert bytes(inst) == b'\x00\x00\x22\x11'


def test_unitialized_convert_to_bytes() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    inst = Pos()
    assert bytes(inst) == b'\x00\x00\x00\x00'


def test_unitialized_substruct_change() -> None:
    class Child(Struct):
        field: UInt8

    class Parent(Struct):
        child: Child

    inst = Parent()
    inst.child = (0x12, )
    assert bytes(inst) == b'\x12'


def test_int_member_assignment() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    class Size(Struct):
        width: UInt8
        height: UInt8

    class Rect(Struct):
        pos: Pos
        size: Size

    rect = Rect(0)
    rect.pos.y = 0x1234
    rect.size.width = 0x56
    assert rect.pos.x == 0
    assert rect.pos.y == 0x1234
    assert rect.size.height == 0
    assert rect.size.width == 0x56

    assert bytes(rect) == b'\x00\x00\x34\x12\x56\x00'


def test_substruct_member_assignment() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    class Size(Struct):
        width: UInt8
        height: UInt8

    class Rect(Struct):
        pos: Pos
        size: Size

    rect1 = Rect(0)
    rect2 = Rect(0)
    rect1.pos.x = 0x0123
    rect1.pos.y = b'\x67\x45'
    rect1.size.width = UInt8(0x11)
    rect1.size.height = 0x22
    rect2.pos.x = 0x89AB
    rect2.pos.y = 0xCDEF
    rect2.size.width = 0x33
    rect2.size.height = 0x44

    assert bytes(rect1) == b'\x23\x01\x67\x45\x11\x22'
    assert bytes(rect2) == b'\xAB\x89\xEF\xCD\x33\x44'


def test_substruct_assignment() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    class Rect(Struct):
        point1: Pos
        point2: Pos

    rect = Rect((Pos((0, 0)), Pos((0, 0))))
    point2_ref = rect.point2

    rect.point1 = Pos((0x0123, 0x4567))
    rect.point2 = b'\x89\xab\xcd\xef'

    # pylint: disable=no-member

    assert rect.point1.x == 0x0123
    assert rect.point1.y == 0x4567
    assert point2_ref.x == 0xab89
    assert point2_ref.y == 0xefcd

    rect.point2 = (0x1122, 0x3344)
    assert point2_ref.x == 0x1122
    assert point2_ref.y == 0x3344

    rect.point2 = 0
    assert point2_ref.x == 0
    assert point2_ref.y == 0

    with raises(TypeError):
        rect.point2 = 'bad value'  # type: ignore


def test_multilevel_assignment() -> None:
    class Child(Struct):
        a: UInt8
        b: UInt8

    class Intermediate(Struct):
        child1: Child
        child2: Child

    class Parent(Struct):
        field1: Intermediate
        field2: Intermediate

    inst = Parent(b'\x00\x11\x22\x33\x44\x55\x66\x77')
    child1_2 = inst.field1.child2  # pylint: disable=no-member
    inst.field1 = (Child((1, 2)), Child((3, 4)))

    assert child1_2.a == 3
    assert child1_2.b == 4


def test_padding_annotation() -> None:
    class SomeStruct(Struct):
        _pad1: Padding[Literal[2]]
        field1: UInt8
        field2: UInt16
        _pad2: Padding[Literal[1]]
        _pad3: Padding[Literal[1]]
        field3: UInt16
        _pad4: Padding[Literal[2]]

    assert sizeof(SomeStruct) == 11
    assert offsetof(SomeStruct, 'field1') == 2
    assert offsetof(SomeStruct, 'field2') == 3
    assert offsetof(SomeStruct, 'field3') == 7

    data = SomeStruct((0x12, 0x3456, 0x789a))
    assert bytes(data) == b'\x00\x00\x12\x56\x34\x00\x00\x9a\x78\x00\x00'


def test_padding_classvar() -> None:
    class SomeStruct(Struct):
        _pad1 = Padding(2)
        field1 = UInt8()
        field2 = UInt16()
        _pad2 = Padding(1)
        _pad3 = Padding(1)
        field3 = UInt16()
        _pad4 = Padding(2)

    assert sizeof(SomeStruct) == 11
    assert offsetof(SomeStruct, 'field1') == 2
    assert offsetof(SomeStruct, 'field2') == 3
    assert offsetof(SomeStruct, 'field3') == 7

    data = SomeStruct((0x12, 0x3456, 0x789a))
    assert bytes(data) == b'\x00\x00\x12\x56\x34\x00\x00\x9a\x78\x00\x00'


def test_shifted_annotation() -> None:
    class SomeStruct(Struct):
        field1: Annotated[UInt8, Shift(1)]
        field2: UInt16
        field3: Annotated[UInt16, Shift(3)]

    assert sizeof(SomeStruct) == 9
    assert sizeof(SomeStruct.field1) == 1
    assert sizeof(SomeStruct.field2) == 2
    assert sizeof(SomeStruct.field3) == 2
    assert offsetof(SomeStruct, 'field1') == 1
    assert offsetof(SomeStruct, 'field2') == 2
    assert offsetof(SomeStruct, 'field3') == 7

    data = SomeStruct((0x12, 0x3456, 0x789a))
    assert bytes(data) == b'\x00\x12\x56\x34\x00\x00\x00\x9a\x78'


def test_shifted_classvar() -> None:
    class SomeStruct(Struct):
        field1 = shifted(UInt8, 1)
        field2 = UInt16()
        field3 = shifted(UInt16, 3)

    assert sizeof(SomeStruct) == 9
    assert sizeof(SomeStruct.field1) == 1
    assert sizeof(SomeStruct.field2) == 2
    assert sizeof(SomeStruct.field3) == 2
    assert offsetof(SomeStruct, 'field1') == 1
    assert offsetof(SomeStruct, 'field2') == 2
    assert offsetof(SomeStruct, 'field3') == 7

    data = SomeStruct((0x12, 0x3456, 0x789a))
    assert bytes(data) == b'\x00\x12\x56\x34\x00\x00\x00\x9a\x78'


def test_padded_annotation() -> None:
    class SomeStruct(Struct):
        field1: Annotated[UInt8, Padding(2)]
        field2: UInt16
        field3: Annotated[UInt16, Padding(3)]

    assert sizeof(SomeStruct) == 10
    assert sizeof(SomeStruct.field1) == 1
    assert sizeof(SomeStruct.field2) == 2
    assert sizeof(SomeStruct.field3) == 2
    assert offsetof(SomeStruct, 'field1') == 0
    assert offsetof(SomeStruct, 'field2') == 3
    assert offsetof(SomeStruct, 'field3') == 5

    data = SomeStruct((0x12, 0x3456, 0x789a))
    assert bytes(data) == b'\x12\x00\x00\x56\x34\x9a\x78\x00\x00\x00'


def test_padded_classvar() -> None:
    class SomeStruct(Struct):
        field1 = padded(UInt8, 2)
        field2 = UInt16()
        field3 = padded(UInt16, 3)

    assert sizeof(SomeStruct) == 10
    assert sizeof(SomeStruct.field1) == 1
    assert sizeof(SomeStruct.field2) == 2
    assert sizeof(SomeStruct.field3) == 2
    assert offsetof(SomeStruct, 'field1') == 0
    assert offsetof(SomeStruct, 'field2') == 3
    assert offsetof(SomeStruct, 'field3') == 5

    data = SomeStruct((0x12, 0x3456, 0x789a))
    assert bytes(data) == b'\x12\x00\x00\x56\x34\x9a\x78\x00\x00\x00'


def test_modifiers_annotation() -> None:
    class SomeStruct(Struct):
        field1: Annotated[UInt8, Padding(2), Shift(2)]
        _pad: Padding[Literal[1]]
        field2: Annotated[UInt16, Shift(1), Padding(1)]
        field3: UInt16

    assert sizeof(SomeStruct) == 12
    assert sizeof(SomeStruct.field1) == 1
    assert sizeof(SomeStruct.field2) == 2
    assert sizeof(SomeStruct.field3) == 2
    assert offsetof(SomeStruct, 'field1') == 2
    assert offsetof(SomeStruct, 'field2') == 7
    assert offsetof(SomeStruct, 'field3') == 10

    data = SomeStruct((0x12, 0x3456, 0x789a))
    assert bytes(data) == b'\x00\x00\x12\x00\x00\x00\x00\x56\x34\x00\x9a\x78'


def test_modifiers_classvar() -> None:
    class SomeStruct(Struct):
        field1 = padded(shifted(UInt8, 2), 2)
        _pad = Padding(1)
        field2 = shifted(padded(UInt16, 1), 1)
        field3 = UInt16()

    assert sizeof(SomeStruct) == 12
    assert sizeof(SomeStruct.field1) == 1
    assert sizeof(SomeStruct.field2) == 2
    assert sizeof(SomeStruct.field3) == 2
    assert offsetof(SomeStruct, 'field1') == 2
    assert offsetof(SomeStruct, 'field2') == 7
    assert offsetof(SomeStruct, 'field3') == 10

    data = SomeStruct((0x12, 0x3456, 0x789a))
    assert bytes(data) == b'\x00\x00\x12\x00\x00\x00\x00\x56\x34\x00\x9a\x78'
