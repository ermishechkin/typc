from __future__ import annotations

from typc import Struct, UInt8, UInt16, UInt32, Union


def test_struct_as_member() -> None:
    class Child(Struct):
        field1: UInt8
        field2: UInt16

    class Data(Union):
        u16: UInt16
        child: Child
        u8: UInt8

    data = Data(0)

    data.child.field1 = 0x12
    assert data.u16 == 0x12
    assert data.u8 == 0x12

    data.child.field2 = 0x3456
    assert data.u16 == 0x5612
    assert data.u8 == 0x12


def test_changed_full() -> None:
    class Child(Struct):
        field1: UInt8
        field2: UInt8

    class Data(Union):
        u16: UInt16
        child: Child

    data = Data()
    struct_ref = data.child

    data.u16 = 0x1234
    assert struct_ref.field1 == 0x34
    assert struct_ref.field2 == 0x12


def test_changed_begin() -> None:
    class Child(Struct):
        field1: UInt16
        field2: UInt8
        field3: UInt32

    class Data(Union):
        child: Child
        ui16: UInt16

    data = Data()
    struct_ref = data.child

    data.ui16 = 0x1234
    assert struct_ref.field1 == 0x1234
    assert struct_ref.field2 == 0
    assert struct_ref.field3 == 0
    assert bytes(struct_ref) == b'\x34\x12\x00\x00\x00\x00\x00'


def test_changed_mid() -> None:
    class Child1(Struct):
        field1: UInt16
        field2: UInt8
        field3: UInt16

    class Child2(Struct):
        field1: UInt8
        field2: UInt8
        field3: UInt8

    class Data(Union):
        child1: Child1
        child2: Child2

    data = Data()
    struct_ref = data.child1

    data.child2.field3 = 0x12
    assert struct_ref.field1 == 0
    assert struct_ref.field2 == 0x12
    assert struct_ref.field3 == 0
    assert bytes(struct_ref) == b'\x00\x00\x12\x00\x00'


def test_changed_end() -> None:
    class Child1(Struct):
        field1: UInt16
        field2: UInt8
        field3: UInt16

    class Child2(Struct):
        field1: UInt8
        field2: UInt16
        field3: UInt16
        field4: UInt8

    class Data(Union):
        child1: Child1
        child2: Child2

    data = Data()
    struct_ref = data.child1

    data.child2.field3 = 0x1234
    assert struct_ref.field1 == 0
    assert struct_ref.field2 == 0
    assert struct_ref.field3 == 0x1234
    assert bytes(struct_ref) == b'\x00\x00\x00\x34\x12'


def test_changed_part_begin() -> None:
    class Child1(Struct):
        field1: UInt32
        field2: UInt8

    class Child2(Struct):
        field1: UInt16
        field2: UInt16

    class Data(Union):
        child1: Child1
        child2: Child2

    data = Data()
    struct_ref = data.child1

    data.child2.field1 = 0x1234
    assert struct_ref.field1 == 0x1234
    assert struct_ref.field2 == 0
    assert bytes(struct_ref) == b'\x34\x12\x00\x00\x00'


def test_changed_part_mid_one() -> None:
    class Child1(Struct):
        field1: UInt8
        field2: UInt16
        field3: UInt32

    class Child2(Struct):
        field1: UInt8
        field2: UInt8
        field3: UInt8
        field4: UInt16

    class Data(Union):
        child1: Child1
        child2: Child2

    data = Data()
    struct_ref = data.child1

    data.child2.field3 = 0x12
    assert struct_ref.field1 == 0
    assert struct_ref.field2 == 0x1200
    assert struct_ref.field3 == 0
    assert bytes(struct_ref) == b'\x00\x00\x12\x00\x00\x00\x00'


def test_changed_many() -> None:
    class Child1(Struct):
        field1: UInt8
        field2: UInt16
        field3: UInt8
        field4: UInt32
        field5: UInt16

    class Child2(Struct):
        field1: UInt16
        field2: UInt32

    class Data(Union):
        child1: Child1
        child2: Child2

    data = Data()
    struct_ref = data.child1

    data.child2.field2 = 0x12345678
    assert struct_ref.field1 == 0
    assert struct_ref.field2 == 0x7800
    assert struct_ref.field3 == 0x56
    assert struct_ref.field4 == 0x1234
    assert struct_ref.field5 == 0
    assert bytes(struct_ref) == b'\x00\x00\x78\x56\x34\x12\x00\x00\x00\x00'


def test_changed_multilevel_src_1() -> None:
    class Child1(Struct):
        field1_1: UInt8
        field1_2: UInt8

    class Child2(Struct):
        field2_1: UInt8
        field2_2: UInt16

    class Intermediate(Struct):
        child1: Child1
        child2: Child2

    class Child3(Struct):
        field3_1: UInt16
        field3_2: UInt16
        field3_3: UInt8

    class Data(Union):
        sub1: Intermediate
        sub2: Child3

    data = Data(b'\x11\x22\x33\x44\x55')
    struct_ref = data.sub2

    data.sub1.child2.field2_1 = 0x12
    assert struct_ref.field3_2 == 0x4412
    assert bytes(struct_ref) == b'\x11\x22\x12\x44\x55'


def test_changed_multilevel_src_2() -> None:
    class Child1(Struct):
        field1_1: UInt8
        field1_2: UInt8

    class Child2(Struct):
        field2_1: UInt8
        field2_2: UInt16

    class Intermediate(Struct):
        child1: Child1
        child2: Child2

    class Child3(Struct):
        field3_1: UInt16
        field3_2: UInt16
        field3_3: UInt32

    class Data(Union):
        sub1: Intermediate
        sub2: Child3

    data = Data(b'\x11\x22\x33\x44\x55\x66\x77\x88')
    struct_ref = data.sub2

    data.sub1.child2 = b'\x78\x9a\xcd'
    assert struct_ref.field3_1 == 0x2211
    assert struct_ref.field3_2 == 0x9a78
    assert struct_ref.field3_3 == 0x887766cd
    assert bytes(struct_ref) == b'\x11\x22\x78\x9a\xcd\x66\x77\x88'


def test_changed_multilevel_dst() -> None:
    class Child1(Struct):
        field1_1: UInt8
        field1_2: UInt8

    class Child2(Struct):
        field2_1: UInt8
        field2_2: UInt16

    class Intermediate(Struct):
        child1: Child1
        child2: Child2

    class Child3(Struct):
        field3_1: UInt16
        field3_2: UInt16
        field3_3: UInt8

    class Data(Union):
        sub1: Intermediate
        sub2: Child3

    data = Data(b'\x11\x22\x33\x44\x55')
    struct_ref = data.sub1

    data.sub2.field3_2 = 0x1234
    assert struct_ref.child2.field2_1 == 0x34
    assert struct_ref.child2.field2_2 == 0x5512
    assert bytes(struct_ref.child1) == b'\x11\x22'
    assert bytes(struct_ref.child2) == b'\x34\x12\x55'


def test_shifted_in_union() -> None:
    class StructChild(Struct):
        field0_1: UInt8
        field0_2: UInt8

    class Struct1(Struct):
        field1_1: StructChild
        field1_2: StructChild

    class Struct2(Struct):
        field2_0: UInt8
        field2_1: Struct1
        field2_2: Struct1

    class Struct3(Struct):
        field3_1: UInt16
        field3_2: UInt16
        field3_3: UInt16
        field3_4: UInt16

    class SomeUnion(Union):
        field_a: Struct2
        field_b: Struct3

    union = SomeUnion(0)
    union.field_a.field2_2.field1_2.field0_1 = 0x12

    assert union.field_b.field3_4 == 0x1200
    assert bytes(union) == b'\x00\x00\x00\x00\x00\x00\x00\x12\x00'
