from __future__ import annotations

from pytest import raises
from typc import (ForwardRef, Pointer16, Pointer32, Struct, UInt8, UInt16,
                  UInt32, UInt64, Union, Void, sizeof, typeof)


class SomeStruct(Struct):
    field1: UInt8
    field2: UInt16


def test_create_getitem_type() -> None:
    ptr_t = Pointer32[SomeStruct]
    assert ptr_t.int_type() is UInt32
    assert ptr_t.ref_type() is SomeStruct
    assert sizeof(ptr_t) == 4


def test_create_getitem_type_bad() -> None:
    ptr_t = Pointer32[int]  # type: ignore
    with raises(TypeError):
        ptr_t(0)  # type: ignore


def test_create_getitem_value() -> None:
    ptr_t = Pointer32[SomeStruct]
    ptr = ptr_t(0x1234)
    assert ptr.int_type() is UInt32
    assert ptr.ref_type() is SomeStruct
    assert sizeof(ptr) == 4
    assert typeof(ptr) is ptr_t


def test_create_new() -> None:
    ptr = Pointer32(SomeStruct, 0x1234)
    ptr_t = typeof(ptr)
    assert ptr_t.int_type() is UInt32
    assert ptr_t.ref_type() is SomeStruct
    assert sizeof(ptr_t) == 4
    assert sizeof(ptr) == 4


def test_init_bytes_1() -> None:
    ptr_t = Pointer32[SomeStruct]
    ptr = ptr_t(b'\x12\x34\x56\x78')
    assert ptr.get() == 0x78563412


def test_init_bytes_2() -> None:
    ptr = Pointer32(SomeStruct, b'\x12\x34\x56\x78')
    assert ptr.get() == 0x78563412


def test_init_int_1() -> None:
    ptr_t = Pointer32[SomeStruct]
    ptr = ptr_t(0x1234)
    assert ptr.get() == 0x1234


def test_init_int_2() -> None:
    ptr = Pointer32(SomeStruct, 0x1234)
    assert ptr.get() == 0x1234


def test_init_another_1() -> None:
    ptr_t = Pointer32[SomeStruct]
    ptr1 = Pointer32(SomeStruct, 0x1234)
    ptr2 = ptr_t(ptr1)
    assert ptr2.get() == 0x1234


def test_init_another_2() -> None:
    ptr1 = Pointer32(SomeStruct, 0x1234)
    ptr2 = Pointer32(SomeStruct, ptr1)
    assert ptr2.get() == 0x1234


def test_init_none_1() -> None:
    ptr_t = Pointer32[SomeStruct]
    ptr = ptr_t()
    assert ptr.get() == 0


def test_init_none_2() -> None:
    ptr = Pointer32(SomeStruct)
    assert ptr.get() == 0


def test_init_bad_1() -> None:
    ptr_t = Pointer32[SomeStruct]
    with raises(TypeError):
        _ = ptr_t('Bad value')  # type: ignore


def test_init_bad_2() -> None:
    with raises(TypeError):
        _ = Pointer32(SomeStruct, 'Bad value')  # type: ignore


def test_int_cast() -> None:
    ptr = Pointer32(SomeStruct, 0x1234)
    assert int(ptr) == 0x1234


def test_bytes_cast() -> None:
    ptr = Pointer32(SomeStruct, 0x1234)
    assert bytes(ptr) == b'\x34\x12\x00\x00'


def test_struct_member_annotation() -> None:
    class Container(Struct):
        ptr: Pointer32[SomeStruct]

    data = Container()
    assert data.ptr.get() == 0
    assert bytes(data) == b'\x00\x00\x00\x00'


def test_struct_member_classvar() -> None:
    class Container(Struct):
        ptr = Pointer32(SomeStruct)

    data = Container()
    assert data.ptr.get() == 0
    assert bytes(data) == b'\x00\x00\x00\x00'


def test_member_zero_init() -> None:
    class Container(Struct):
        ptr: Pointer16[SomeStruct]
        field: UInt32

    inst = Container()
    assert inst.ptr.get() == 0


def test_member_change_1() -> None:
    class Container(Struct):
        ptr: Pointer16[SomeStruct]
        field: UInt32

    inst = Container()
    inst.ptr = 0x1234
    assert int(inst.ptr) == 0x1234


def test_member_change_2() -> None:
    class Container(Struct):
        ptr: Pointer16[SomeStruct]
        field: UInt32

    inst = Container()
    ptr = inst.ptr

    inst.ptr = 0x1234
    assert int(ptr) == 0x1234

    ptr.set(0x5678)  # pylint: disable=no-member
    assert int(inst.ptr) == 0x5678


def test_union_full() -> None:
    class Container(Union):
        ptr: Pointer32[SomeStruct]
        u32: UInt32
        u64: UInt64

    inst = Container(b'\x11\x22\x33\x44\x55\x66\x77\x88')
    assert inst.ptr.get() == 0x44332211

    inst.u32 = 0x12345678
    assert inst.ptr.get() == 0x12345678


def test_union_begin() -> None:
    class Container(Union):
        ptr: Pointer32[SomeStruct]
        u16: UInt16
        u64: UInt64

    inst = Container(b'\x11\x22\x33\x44\x55\x66\x77\x88')
    assert inst.ptr.get() == 0x44332211

    inst.u16 = 0x1234
    assert inst.ptr.get() == 0x44331234


def test_union_end() -> None:
    class TwoInt(Struct):
        field1: UInt16
        field2: UInt16

    class Container(Union):
        ptr: Pointer32[SomeStruct]
        twoint: TwoInt
        u64: UInt64

    inst = Container(b'\x11\x22\x33\x44\x55\x66\x77\x88')
    assert inst.ptr.get() == 0x44332211

    inst.twoint.field2 = 0x1234
    assert inst.ptr.get() == 0x12342211


def test_void_1() -> None:
    ptr_t = Pointer32[Void]
    assert ptr_t.int_type() is UInt32
    assert ptr_t.ref_type() is Void
    assert sizeof(ptr_t) == 4

    ptr = ptr_t(0x12)
    assert ptr.int_type() is UInt32
    assert ptr.ref_type() is Void
    assert sizeof(ptr) == 4


def test_void_2() -> None:
    ptr = Pointer32(Void, 0x12)
    assert ptr.int_type() is UInt32
    assert ptr.ref_type() is Void
    assert sizeof(ptr) == 4

    ptr_t = typeof(ptr)
    assert ptr_t.int_type() is UInt32
    assert ptr_t.ref_type() is Void
    assert sizeof(ptr_t) == 4


def test_forward_annotation() -> None:
    class StructA(Struct):
        ptr: Pointer32[ForwardRef]

    class StructB(Struct):
        field_b: UInt32

    assert StructA.ptr.ref_type() is Void

    StructA.ptr.set_ref_type(StructB)
    assert StructA.ptr.ref_type() is StructB


def test_forward_classvar() -> None:
    class StructA(Struct):
        ptr = Pointer32(ForwardRef)

    class StructB(Struct):
        field_b = UInt32()

    assert StructA.ptr.ref_type() is Void

    StructA.ptr.set_ref_type(StructB)
    assert StructA.ptr.ref_type() is StructB


def test_forward_multiple_updates() -> None:
    class StructA(Struct):
        ptr = Pointer32(ForwardRef)

    class StructB(Struct):
        field_b = UInt32()

    StructA.ptr.set_ref_type(StructB)
    with raises(TypeError):
        StructA.ptr.set_ref_type(SomeStruct)


def test_forward_bad() -> None:
    class StructA(Struct):
        ptr = Pointer32(ForwardRef)

    with raises(TypeError):
        StructA.ptr.set_ref_type('Bad type')  # type: ignore
