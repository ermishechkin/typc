from __future__ import annotations

from typing import Literal

from pytest import raises
from typc import (Array, Struct, UInt8, UInt16, clone_type, sizeof, type_name,
                  typeof)


def test_array_init() -> None:
    array = Array(UInt8, 4)
    assert bytes(array) == b'\x00\x00\x00\x00'

    array = Array(UInt8, 4, None)
    assert bytes(array) == b'\x00\x00\x00\x00'

    array = Array(UInt8, 4, 0)
    assert bytes(array) == b'\x00\x00\x00\x00'

    array = Array(UInt8, 4, (b'\x00', b'\x11', b'\x22', b'\x33'))
    assert bytes(array) == b'\x00\x11\x22\x33'

    array = Array(UInt8, 4, (0x00, 0x11, 0x22, 0x33))
    assert bytes(array) == b'\x00\x11\x22\x33'

    array = Array(UInt8, 4, b'\x00\x11\x22\x33')
    assert bytes(array) == b'\x00\x11\x22\x33'

    array = Array(UInt8, 4, Array(UInt8, 4, (1, 2, 3, 4)))
    assert bytes(array) == b'\x01\x02\x03\x04'

    with raises(TypeError):
        Array(int, 4, b'\x01\x02\x03\x04')  # type: ignore

    with raises(TypeError):
        Array(UInt8, 4, 'bad value')  # type: ignore


def test_array_init_getitem() -> None:
    arr_t = Array[UInt16, Literal[3]]

    arr1 = arr_t(b'\x11\x22\x33\x44\x55\x66')
    assert arr1[0] == 0x2211
    assert arr1[1] == 0x4433
    assert arr1[2] == 0x6655

    arr2 = arr_t((0x1122, 0x3344, 0x5566))
    assert bytes(arr2) == b'\x22\x11\x44\x33\x66\x55'

    arr3 = arr_t(Array(UInt16, 3, (0x1122, 0x3344, 0x5566)))
    assert bytes(arr3) == b'\x22\x11\x44\x33\x66\x55'


def test_array_init_getitem_bad() -> None:
    with raises(TypeError):
        arr_t = Array[int, Literal[3]]  # type: ignore
        arr_t((1, 2, 3))  # type: ignore


def test_array_atom_item_modifications() -> None:
    array = Array(UInt8, 4)
    assert bytes(array) == b'\x00\x00\x00\x00'

    array[1] = 0x11
    array[2] = 0x22
    assert bytes(array) == b'\x00\x11\x22\x00'

    array[3] = b'\x33'
    assert bytes(array) == b'\x00\x11\x22\x33'
    assert array[3] == 0x33


def test_array_complex_item_modifications() -> None:
    class Pos(Struct):
        x: UInt8
        y: UInt8

    array = Array(Pos, 2)
    assert bytes(array) == b'\x00\x00\x00\x00'

    saved_el = array[1]
    assert bytes(saved_el) == b'\x00\x00'

    array[0] = Pos((1, 2))
    array[1] = Pos((3, 4))
    assert bytes(array) == b'\x01\x02\x03\x04'
    assert bytes(saved_el) == b'\x03\x04'

    array[1].x = 5
    array[1].y = 6
    assert bytes(array) == b'\x01\x02\x05\x06'
    assert bytes(saved_el) == b'\x05\x06'


def test_struct_member_annotation() -> None:
    class SomeStruct(Struct):
        field2: Array[UInt16, Literal[4]]

    data = SomeStruct()
    assert bytes(data) == b'\x00\x00\x00\x00\x00\x00\x00\x00'


def test_struct_member_classvar() -> None:
    class SomeStruct(Struct):
        field2 = Array(UInt16, 4)

    data = SomeStruct()
    assert bytes(data) == b'\x00\x00\x00\x00\x00\x00\x00\x00'


def test_sizeof() -> None:
    class SomeStruct(Struct):
        field = Array(UInt16, 4)

    data = SomeStruct(0)
    arr_t = SomeStruct.field
    arr = data.field
    assert sizeof(arr_t) == 8
    assert sizeof(arr) == 8
    assert arr_t.length() == 4
    assert arr.length() == 4
    assert len(arr) == 4


def test_typeof() -> None:
    class SomeStruct(Struct):
        field = Array(UInt16, 4)

    data = SomeStruct(0)
    arr_t = SomeStruct.field
    arr = data.field
    assert typeof(arr) is arr_t
    assert arr_t.item_type() is UInt16
    assert arr.item_type() is UInt16


def test_name() -> None:
    data = Array(UInt16, 4)
    arr_t = typeof(data)
    assert type_name(arr_t) == 'uint16_t[4]'
    assert type_name(data) == 'uint16_t[4]'


def test_clone() -> None:
    arr_t = typeof(Array(UInt16, 4))
    clone = clone_type(arr_t)
    assert clone is not arr_t
    assert clone.item_type() is UInt16
    assert clone.length() == 4
    assert type_name(clone) == 'uint16_t[4]'

    clone2 = clone_type(clone, name='uint16x4')
    assert type_name(clone2) == 'uint16x4'

    clone3 = clone_type(clone2)
    assert type_name(clone3) == 'uint16x4'


def test_array_as_struct_member_simple() -> None:
    class SomeStruct(Struct):
        field1: UInt8
        field2: Array[UInt8, Literal[4]]
        field3: UInt16

    inst = SomeStruct()
    assert bytes(inst) == b'\x00\x00\x00\x00\x00\x00\x00'

    inst.field2 = (1, 2, 3, 4)
    assert bytes(inst) == b'\x00\x01\x02\x03\x04\x00\x00'

    inst.field2 = (b'\x05', b'\x06', b'\x07', b'\x08')
    assert bytes(inst) == b'\x00\x05\x06\x07\x08\x00\x00'

    inst.field2 = b'\x09\x0a\x0b\x0c'
    assert bytes(inst) == b'\x00\x09\x0a\x0b\x0c\x00\x00'

    inst.field2 = Array(UInt8, 4, (0x11, 0x22, 0x33, 0x44))
    assert bytes(inst) == b'\x00\x11\x22\x33\x44\x00\x00'

    inst.field2 = 0
    assert bytes(inst) == b'\x00\x00\x00\x00\x00\x00\x00'

    with raises(TypeError):
        inst.field2 = 'bad value'  # type: ignore


def test_array_as_struct_member_complex() -> None:
    class Pos(Struct):
        x: UInt8
        y: UInt8

    class SomeStruct(Struct):
        field1: UInt8
        field2: Array[Pos, Literal[2]]
        field3: UInt16

    inst = SomeStruct()
    substruct = inst.field2[1]

    inst.field2 = (Pos((0x55, 0x66)), Pos((0x77, 0x88)))
    assert substruct.x == 0x77

    inst.field2 = (b'\x99\xaa', b'\xbb\xcc')
    assert substruct.x == 0xbb

    inst.field2 = b'\x11\x22\x33\x44'
    assert substruct.x == 0x33

    inst.field2 = Array(Pos, 2, b'\x12\x34\x56\x78')
    assert bytes(inst) == b'\x00\x12\x34\x56\x78\x00\x00'

    inst.field2 = 0
    assert substruct.x == 0


def test_array_uninitialized_getitem() -> None:
    array = Array(UInt8, 4)
    assert array[2] == 0


def test_array_uninitialized_setitem() -> None:
    array = Array(UInt8, 4)
    array[2] = 0x11
    assert bytes(array) == b'\x00\x00\x11\x00'


def test_array_uninitialized_reset_member() -> None:
    class SomeStruct(Struct):
        field1: UInt8
        field2: Array[UInt8, Literal[4]]
        field3: UInt16

    inst = SomeStruct()
    inst.field2 = Array(UInt8, 4, (0x11, 0x22, 0x33, 0x44))
    assert bytes(inst) == b'\x00\x11\x22\x33\x44\x00\x00'


def test_eq() -> None:
    arr1_t = typeof(Array(UInt16, 4))
    arr2_t = typeof(Array(UInt8, 4))
    arr3_t = typeof(Array(UInt8, 8))
    arr4_t = typeof(Array(UInt16, 4))
    assert arr1_t == arr1_t  # pylint: disable=comparison-with-itself
    assert arr1_t != arr2_t
    assert arr1_t != arr3_t
    assert arr1_t == arr4_t

    assert arr1_t != UInt16
    assert arr1_t != Array
    assert arr1_t != list
