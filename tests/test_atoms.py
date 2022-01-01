from __future__ import annotations

from operator import index

from pytest import raises
from typc import (Float, Int16, Integer, Real, Struct, UInt8, UInt16, Union,
                  clone_type, sizeof, type_name, typeof)


def test_zero_init() -> None:
    class SomeStruct(Struct):
        field: UInt16

    assert SomeStruct.field is UInt16


def test_init_zero() -> None:
    class SomeStruct(Struct):
        field: Float

    data = SomeStruct()
    data.field = Float(0)
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


def test_init_bad_size() -> None:
    class SomeStruct(Struct):
        field: UInt16

    data = SomeStruct()
    with raises(ValueError):
        data.field = UInt16(b'\x11\x22\x33')


def test_type_typeof() -> None:
    class SomeStruct(Struct):
        field: UInt16

    data = SomeStruct()
    assert typeof(data.field) == UInt16


def test_type_sizeof() -> None:
    class SomeStruct(Struct):
        field: UInt16

    data = SomeStruct()
    assert sizeof(SomeStruct.field) == 2
    assert sizeof(data.field) == 2


def test_name() -> None:
    class SomeStruct(Struct):
        field: UInt16

    data = SomeStruct()
    assert type_name(SomeStruct.field) == 'uint16_t'
    assert type_name(data.field) == 'uint16_t'


def test_clone() -> None:
    clone = clone_type(Float)
    data = clone(0)
    assert clone is not Float
    assert sizeof(clone) == 4
    assert type_name(clone) == 'float'
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


def test_typechecks_meta() -> None:
    clone16 = clone_type(UInt16, name='Word')
    value = clone16(0x1234)

    assert not isinstance(Integer, Integer)
    assert issubclass(Integer, Integer)

    assert not isinstance(clone16, Integer)
    assert issubclass(clone16, Integer)

    assert isinstance(value, Integer)
    with raises(TypeError):
        issubclass(value, Integer)  # type: ignore

    assert not isinstance('string', Integer)
    with raises(TypeError):
        issubclass('string', Integer)  # type: ignore


def test_typechecks_meta_another() -> None:
    clone16 = clone_type(UInt16, name='Word')
    value = clone16(0x1234)

    assert not isinstance(Integer, Real)
    assert not issubclass(Integer, Real)

    assert not isinstance(clone16, Real)
    assert not issubclass(clone16, Real)

    assert not isinstance(value, Real)
    with raises(TypeError):
        issubclass(value, Real)  # type: ignore


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


def test_member_change_bytes() -> None:
    class SomeStruct(Struct):
        field_a: UInt8
        field_b: UInt16

    inst = SomeStruct()
    inst.field_b = b'\x11\x22'
    assert bytes(inst) == b'\x00\x11\x22'


def test_member_change_another() -> None:
    class SomeStruct(Struct):
        field_a: UInt8
        field_b: UInt16

    inst = SomeStruct()
    inst.field_b = 0x1234
    assert bytes(inst) == b'\x00\x34\x12'


def test_member_change_zero() -> None:
    class SomeStruct(Struct):
        field_a: UInt8
        field_b: UInt16

    inst = SomeStruct(b'\x11\x22\x33')
    inst.field_b = 0
    assert bytes(inst) == b'\x11\x00\x00'


def test_member_change_bad_type() -> None:
    class SomeStruct(Struct):
        field_a: UInt8
        field_b: UInt16

    inst = SomeStruct()
    with raises(TypeError):
        inst.field_b = 'Bad value'  # type: ignore


def test_member_change_bad_size() -> None:
    class SomeStruct(Struct):
        field_a: UInt8
        field_b: UInt16

    inst = SomeStruct()
    with raises(ValueError):
        inst.field_b = b'\x11'


def test_union_full() -> None:
    class Container(Union):
        field_a: UInt16
        field_b: UInt16

    inst = Container(b'\x11\x22')
    assert bytes(inst) == b'\x11\x22'

    inst.field_a = 0x1234
    assert bytes(inst.field_b) == b'\x34\x12'


def test_union_begin() -> None:
    class Container(Union):
        field_a: UInt8
        field_b: UInt16

    inst = Container(b'\x11\x22')
    assert bytes(inst) == b'\x11\x22'

    inst.field_a = 0x12
    assert bytes(inst.field_b) == b'\x12\x22'


def test_union_end() -> None:
    class TwoByte(Struct):
        field1: UInt8
        field2: UInt8

    class Container(Union):
        data: UInt16
        twoint: TwoByte

    inst = Container(b'\x11\x22')
    assert bytes(inst.data) == b'\x11\x22'

    inst.twoint.field2 = 0x44
    assert bytes(inst.data) == b'\x11\x44'


def test_unary_operator() -> None:
    obj = UInt16(10)

    res1 = -obj
    res2 = index(obj)

    assert isinstance(res1, int)
    assert res1 == -10

    assert isinstance(res2, int)
    assert res2 == 10


def test_binary_operator() -> None:
    obj1 = UInt16(10)
    obj2 = UInt16(20)
    obj3 = Float(30.0)

    res1 = obj1 + 1
    res2 = obj1 + 1.0
    res3 = 1 + obj1
    res4 = 1.0 + obj1
    res5 = obj1 + obj2
    res6 = obj1 + obj3

    assert isinstance(res1, int)
    assert res1 == 11

    assert isinstance(res2, float)
    assert res2 == 11.0

    assert isinstance(res3, int)
    assert res3 == 11

    assert isinstance(res4, float)
    assert res4 == 11.0

    assert isinstance(res5, int)
    assert res5 == 30

    assert isinstance(res6, float)
    assert res6 == 40.0


def test_inplace_operator() -> None:
    obj_1 = obj_1_bak = UInt16(10)
    obj_2 = obj_2_bak = UInt16(20)
    obj_3 = obj_3_bak = UInt16(30)
    obj_4 = obj_4_bak = UInt16(40)
    obj_5 = UInt16(50)
    obj_6 = Float(60.9)

    obj_1 += 1
    assert obj_1 is obj_1_bak
    assert obj_1 == 11

    obj_2 += 2.6
    assert obj_2 is obj_2_bak
    assert obj_2 == 22

    obj_3 += obj_5
    assert obj_3 is obj_3_bak
    assert obj_3 == 80

    obj_4 += obj_6
    assert obj_4 is obj_4_bak
    assert obj_4 == 100
