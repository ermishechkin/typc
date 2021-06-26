from __future__ import annotations

from typing import Literal
from typing_extensions import Annotated

from pytest import raises
from typc import (Padding, Shift, Struct, UInt8, UInt16, Union, offsetof,
                  padded, shifted, sizeof, typeof)


def test_declaration_annotations() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    class Data(Union):
        u16: UInt16
        pos: Pos
        u8: UInt8

    assert Data.u16 is UInt16
    assert Data.pos is Pos
    assert Data.u8 is UInt8


def test_declaration_classvars() -> None:
    class Pos(Struct):
        x = UInt16()
        y = UInt16()

    class Data(Union):
        u16 = UInt16()
        pos = Pos()
        u8 = UInt8()

    assert Data.u16 is UInt16
    assert Data.pos is Pos
    assert Data.u8 is UInt8


def test_declaration_mixed() -> None:
    with raises(ValueError):

        class Data(Union):
            u16: UInt16
            u8 = UInt8()

        _ = Data


def test_declaration_empty() -> None:
    with raises(ValueError):

        class EmptyUnion(Union):
            pass

        _ = EmptyUnion


def test_non_type_field_annotation() -> None:
    with raises(ValueError):

        class BadUnion(Union):
            field: str

        _ = BadUnion


def test_non_type_field_classvar() -> None:
    with raises(ValueError):

        class BadUnion(Union):
            field = int

        _ = BadUnion


def test_nonexistent_type_member_get() -> None:
    class SomeUnion(Union):
        field: UInt8

    with raises(AttributeError):
        # pylint: disable=no-member
        _ = SomeUnion.bad  # type: ignore


def test_nonexistent_type_member_set() -> None:
    class SomeUnion(Union):
        field: UInt8

    with raises(AttributeError):
        SomeUnion.bad = 1  # type: ignore


def test_nonexistent_value_member_get() -> None:
    class SomeUnion(Union):
        field: UInt8

    inst = SomeUnion(0)
    with raises(AttributeError):
        # pylint: disable=no-member
        _ = inst.bad  # type: ignore


def test_nonexistent_value_member_set() -> None:
    class SomeUnion(Union):
        field: UInt8

    inst = SomeUnion(0)
    with raises(AttributeError):
        # pylint: disable=attribute-defined-outside-init
        inst.bad = 1  # type: ignore


def test_sizeof() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    class Data(Union):
        u16: UInt16
        pos: Pos
        u8: UInt8

    data = Data(0)
    assert sizeof(Data) == 4
    assert sizeof(data) == 4


def test_typeof() -> None:
    class Data(Union):
        u16: UInt16
        u8: UInt8

    data = Data(0)
    assert typeof(data) is Data


def test_init_zero() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    class Data(Union):
        u16: UInt16
        pos: Pos
        u8: UInt8

    data = Data(0)
    assert data.pos.x == 0
    assert data.pos.y == 0
    assert data.u16 == 0
    assert data.u8 == 0

    assert bytes(data) == b'\x00\x00\x00\x00'


def test_init_bytes() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    class Data(Union):
        u16: UInt16
        pos: Pos
        u8: UInt8

    data = Data(b'\x11\x22\x33\x44')
    assert data.u16 == 0x2211
    assert data.pos.x == 0x2211
    assert data.pos.y == 0x4433
    assert data.u8 == 0x11


def test_init_union() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    class Data(Union):
        u16: UInt16
        pos: Pos
        u8: UInt8

    data1 = Data(b'\x11\x22\x33\x44')
    data2 = Data(data1)

    assert data2.u16 == 0x2211
    assert data2.pos.x == 0x2211
    assert data2.pos.y == 0x4433
    assert data2.u8 == 0x11


def test_init_bad_type() -> None:
    class Data(Union):
        u16: UInt16
        u8: UInt8

    with raises(TypeError):
        Data('Bad value')  # type: ignore


def test_unitialized_member_access() -> None:
    class SomeUnion(Union):
        field1: UInt16
        field2: UInt8

    inst = SomeUnion()
    assert inst.field2 == 0


def test_unitialized_member_assignment() -> None:
    class SomeUnion(Union):
        field1: UInt16
        field2: UInt8

    inst = SomeUnion()
    inst.field2 = 0x11
    assert bytes(inst) == b'\x11\x00'


def test_unitialized_convert_to_bytes() -> None:
    class SomeUnion(Union):
        field1: UInt16
        field2: UInt8

    inst = SomeUnion()
    assert bytes(inst) == b'\x00\x00'


def test_unitialized_substruct_change() -> None:
    class Child(Union):
        field: UInt16

    class Parent(Union):
        child1: UInt8
        child2: Child

    inst = Parent()
    inst.child2 = Child(b'\x12\x34')
    assert bytes(inst) == b'\x12\x34'


def test_intersection_int_and_int() -> None:
    class SomeUnion(Union):
        field_u8: UInt8
        field_u16: UInt16

    inst = SomeUnion(0)
    inst.field_u16 = 0x1234
    assert inst.field_u8 == 0x34
    assert inst.field_u16 == 0x1234
    assert bytes(inst) == b'\x34\x12'

    inst.field_u8 = 0x56
    assert inst.field_u8 == 0x56
    assert inst.field_u16 == 0x1256
    assert bytes(inst) == b'\x56\x12'


def test_intersection_empty() -> None:
    class Child1(Struct):
        field1_1: UInt16
        field1_2: UInt16
        field1_3: UInt16

    class Child2(Struct):
        field2_1: UInt16
        field2_2: UInt16

    class SomeUnion(Union):
        child1: Child1
        child2: Child2

    inst = SomeUnion(0)
    child1_ref = inst.child1
    child2_ref = inst.child2

    inst.child1.field1_3 = 0x1234
    assert child1_ref.field1_1 == 0
    assert child1_ref.field1_2 == 0
    assert child1_ref.field1_3 == 0x1234
    assert child2_ref.field2_1 == 0
    assert child2_ref.field2_2 == 0


def test_member_assignment_int() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    class Data(Union):
        u16: UInt16
        pos: Pos
        u8: UInt8

    data = Data(0)
    data.u16 = 0x1234
    assert data.u16 == 0x1234
    assert data.pos.x == 0x1234
    assert data.pos.y == 0
    assert data.u8 == 0x34
    assert bytes(data) == b'\x34\x12\x00\x00'


def test_member_assignment_substruct() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    class Data(Union):
        u16: UInt16
        pos: Pos
        u8: UInt8

    data = Data(0)
    pos = data.pos
    data.pos = Pos((0x1234, 0x5678))
    assert bytes(data) == b'\x34\x12\x78\x56'
    assert bytes(pos) == b'\x34\x12\x78\x56'


def test_member_assignment_subunion() -> None:
    class Child(Union):
        field1: UInt8
        field2: UInt8

    class Data(Union):
        child: Child
        u16: UInt16
        u8: UInt8

    data = Data(0)
    child = data.child

    data.u16 = b'\x11\xff'
    data.child = b'\x12'
    assert bytes(data) == b'\x12\xff'
    assert bytes(child) == b'\x12'

    data.child = Child(b'\x34')
    assert bytes(data) == b'\x34\xff'
    assert bytes(child) == b'\x34'

    data.child = 0
    assert bytes(data) == b'\x00\xff'
    assert bytes(child) == b'\x00'

    with raises(TypeError):
        data.child = 'Bad value'  # type: ignore


def test_multilevel_assignment() -> None:
    class Child(Union):
        a: UInt8
        b: UInt16

    class Intermediate(Union):
        child1: Child
        child2: UInt8

    class Parent(Union):
        field1: Intermediate
        field2: UInt16

    inst = Parent(b'\x12\x34')
    child1_2 = inst.field1.child1  # pylint: disable=no-member

    inst.field1.child1 = b'\x56\x78'
    assert child1_2.a == 0x56
    assert child1_2.b == 0x7856
    assert inst.field2 == 0x7856

    inst.field1 = b'\xab\xcd'
    assert child1_2.a == 0xab
    assert child1_2.b == 0xcdab
    assert inst.field2 == 0xcdab


def test_padding_annotation() -> None:
    class Child(Struct):
        field1: UInt16
        field2: UInt8
        field3: UInt8

    class Data(Union):
        child: Child
        _pad: Padding[Literal[5]]

    assert sizeof(Data) == 5
    data = Data(b'\x11\x22\x33\x44\x55')
    assert data.child.field3 == 0x44
    assert bytes(data) == b'\x11\x22\x33\x44\x55'


def test_padding_classvar() -> None:
    class Child(Struct):
        field1 = UInt16()
        field2 = UInt8()
        field3 = UInt8()

    class Data(Union):
        child = Child()
        _pad = Padding(5)

    assert sizeof(Data) == 5
    data = Data(b'\x11\x22\x33\x44\x55')
    assert data.child.field3 == 0x44
    assert bytes(data) == b'\x11\x22\x33\x44\x55'


def test_shifted_annotation() -> None:
    class Child1(Struct):
        field1_1: UInt16
        field1_2: UInt8
        field1_3: UInt8

    class Child2(Struct):
        field2_1: UInt8
        field2_2: UInt16
        field2_3: UInt8

    class Data(Union):
        child1: Child1
        child2: Annotated[Child2, Shift(1)]
        child3: Annotated[UInt16, Shift(1)]

    assert sizeof(Data) == 5
    assert offsetof(Data, 'child1') == 0
    assert offsetof(Data, 'child2') == 1
    assert offsetof(Data, 'child3') == 1

    data = Data(0)
    child1 = data.child1
    data.child2.field2_1 = 0x12
    assert child1.field1_1 == 0x1200
    assert data.child3 == 0x12
    assert bytes(data) == b'\x00\x12\x00\x00\x00'

    child1.field1_2 = 0x34
    assert child1.field1_2 == 0x34
    assert data.child3 == 0x3412
    assert bytes(data) == b'\x00\x12\x34\x00\x00'


def test_shifted_classvar() -> None:
    class Child1(Struct):
        field1_1 = UInt16()
        field1_2 = UInt8()
        field1_3 = UInt8()

    class Child2(Struct):
        field2_1 = UInt8()
        field2_2 = UInt16()
        field2_3 = UInt8()

    class Data(Union):
        child1 = Child1()
        child2 = shifted(Child2, 1)
        child3 = shifted(UInt16, 1)

    assert sizeof(Data) == 5
    assert offsetof(Data, 'child1') == 0
    assert offsetof(Data, 'child2') == 1
    assert offsetof(Data, 'child3') == 1

    data = Data(0)
    child1 = data.child1
    data.child2.field2_1 = 0x12
    assert child1.field1_1 == 0x1200
    assert data.child3 == 0x12
    assert bytes(data) == b'\x00\x12\x00\x00\x00'

    child1.field1_2 = 0x34
    assert data.child2.field2_2 == 0x34
    assert data.child3 == 0x3412
    assert bytes(data) == b'\x00\x12\x34\x00\x00'

    child1.field1_1 = 0x5678
    assert data.child2.field2_1 == 0x56
    assert data.child3 == 0x3456
    assert bytes(data) == b'\x78\x56\x34\x00\x00'


def test_padded_annotation() -> None:
    class Child(Struct):
        field1_1: UInt16
        field1_2: UInt16

    class Data(Union):
        child1: Annotated[UInt8, Padding(4)]
        child2: Annotated[UInt16, Padding(1)]
        child3: Child

    assert sizeof(Data) == 5
    assert sizeof(Data.child1) == 1
    assert sizeof(Data.child2) == 2
    assert sizeof(Data.child3) == 4

    data = Data(0)
    data.child2 = 0x1234
    assert data.child1 == 0x34
    assert bytes(data.child3) == b'\x34\x12\x00\x00'


def test_padded_classvar() -> None:
    class Child(Struct):
        field1_1 = UInt16()
        field1_2 = UInt16()

    class Data(Union):
        child1 = padded(UInt8, 4)
        child2 = padded(UInt16, 1)
        child3 = Child()

    assert sizeof(Data) == 5
    assert sizeof(Data.child1) == 1
    assert sizeof(Data.child2) == 2
    assert sizeof(Data.child3) == 4

    data = Data(0)
    data.child2 = 0x1234
    assert data.child1 == 0x34
    assert bytes(data.child3) == b'\x34\x12\x00\x00'
