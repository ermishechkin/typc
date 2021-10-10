from __future__ import annotations

from typing import Literal

from pytest import raises
from typc import (Bytes, Struct, UInt16, UInt32, UInt64, Union, clone_type,
                  sizeof, type_name, typeof)


def test_create_getitem_type() -> None:
    bytes_t = Bytes[Literal[5]]
    assert sizeof(bytes_t) == 5


def test_create_getitem_type_bad() -> None:
    with raises(TypeError):
        _ = Bytes[5]  # type: ignore


def test_create_getitem_value() -> None:
    bytes_t = Bytes[Literal[5]]
    data = bytes_t(b'\x11\x22\x33\x44\x55')
    assert sizeof(bytes_t) == 5
    assert typeof(data) is bytes_t
    assert sizeof(data) == 5
    assert len(data) == 5


def test_create_new() -> None:
    data = Bytes(5, b'\x11\x22\x33\x44\x55')
    bytes_t = typeof(data)
    assert bytes_t.length() == 5
    assert sizeof(bytes_t) == 5
    assert data.length() == 5
    assert sizeof(data) == 5
    assert len(data) == 5


def test_init_short_1() -> None:
    bytes_t = Bytes[Literal[5]]
    data = bytes_t(b'\x11\x22\x33')
    assert bytes(data) == b'\x11\x22\x33\x00\x00'


def test_init_short_2() -> None:
    data = Bytes(5, b'\x11\x22\x33')
    assert bytes(data) == b'\x11\x22\x33\x00\x00'


def test_init_another_1() -> None:
    bytes_t = Bytes[Literal[5]]
    data1 = Bytes(5, b'\x11\x22\x33\x44\x55')
    data2 = bytes_t(data1)
    assert bytes(data2) == b'\x11\x22\x33\x44\x55'


def test_init_another_2() -> None:
    data1 = Bytes(5, b'\x11\x22\x33\x44\x55')
    data2 = Bytes(5, data1)
    assert bytes(data2) == b'\x11\x22\x33\x44\x55'


def test_init_bad_1() -> None:
    bytes_t = Bytes[Literal[5]]
    with raises(TypeError):
        _ = bytes_t('Bad value')  # type: ignore


def test_init_bad_2() -> None:
    with raises(TypeError):
        _ = Bytes(5, 'Bad value')  # type: ignore


def test_init_bad_3() -> None:
    with raises(ValueError):
        _ = Bytes(5, b'too_many_bytes')


def test_init_bad_4() -> None:
    with raises(TypeError):
        _ = Bytes('5', b'\x11\x22\x33\x44\x55')  # type: ignore


def test_name_1() -> None:
    bytes_t = Bytes[Literal[5]]
    data = bytes_t(0)
    assert type_name(bytes_t) == 'char[5]'
    assert type_name(data) == 'char[5]'


def test_name_2() -> None:
    data = Bytes(5, b'abcde')
    bytes_t = typeof(data)
    assert type_name(bytes_t) == 'char[5]'
    assert type_name(data) == 'char[5]'


def test_clone() -> None:
    bytes_t = Bytes[Literal[5]]
    clone = clone_type(bytes_t)
    data = clone(0)
    assert clone is not bytes_t
    assert sizeof(clone) == 5
    assert type_name(clone) == 'char[5]'
    assert bytes(data) == b'\x00\x00\x00\x00\x00'

    clone2 = clone_type(clone, name='str_5')
    assert type_name(clone2) == 'str_5'

    clone3 = clone_type(clone2)
    assert type_name(clone3) == 'str_5'


def test_getitem() -> None:
    data = Bytes(6, b'abcdef')
    assert data[2] == b'c'


def test_getitem_bad_index() -> None:
    data = Bytes(6, b'abcdef')
    with raises(IndexError):
        _ = data[6]


def test_setitem() -> None:
    data = Bytes(6, b'abcdef')
    data[2] = b'X'
    assert bytes(data) == b'abXdef'


def test_setitem_bad_index() -> None:
    data = Bytes(6, b'abcdef')
    with raises(IndexError):
        data[6] = b'X'


def test_setitem_bad_len() -> None:
    data = Bytes(6, b'abcdef')
    with raises(ValueError):
        data[2] = b'XY'


def test_struct_member_annotation() -> None:
    class Container(Struct):
        field: Bytes[Literal[5]]

    data = Container()
    assert data.field.length() == 5
    assert bytes(data.field) == b'\x00\x00\x00\x00\x00'


def test_struct_member_classvar() -> None:
    class Container(Struct):
        field = Bytes(5)

    data = Container()
    assert data.field.length() == 5
    assert bytes(data.field) == b'\x00\x00\x00\x00\x00'


def test_member_change_bytes() -> None:
    class Container(Struct):
        field_b: Bytes[Literal[5]]
        field_u: UInt32

    inst = Container()
    data = inst.field_b
    inst.field_b = b'\x11\x22\x33\x44\x55'
    assert bytes(data) == b'\x11\x22\x33\x44\x55'


def test_member_change_another() -> None:
    class Container(Struct):
        field_b: Bytes[Literal[5]]
        field_u: UInt32

    inst = Container()
    another = Bytes(5, b'\x01\x23\x45\x67\x89')
    data = inst.field_b
    inst.field_b = another
    assert bytes(data) == b'\x01\x23\x45\x67\x89'


def test_member_change_short() -> None:
    class Container(Struct):
        field_b: Bytes[Literal[5]]
        field_u: UInt32

    inst = Container()
    data = inst.field_b
    inst.field_b = b'\x11\x22\x33'
    assert bytes(data) == b'\x11\x22\x33\x00\x00'


def test_member_change_zero() -> None:
    class Container(Struct):
        field_b: Bytes[Literal[5]]
        field_u: UInt32

    inst = Container()
    data = inst.field_b
    inst.field_b = 0
    assert bytes(data) == b'\x00\x00\x00\x00\x00'


def test_member_change_bad_type() -> None:
    class Container(Struct):
        field_b: Bytes[Literal[5]]
        field_u: UInt32

    inst = Container()
    with raises(TypeError):
        inst.field_b = 'Bad value'  # type: ignore


def test_member_change_bad_size() -> None:
    class Container(Struct):
        field_b: Bytes[Literal[5]]
        field_u: UInt32

    inst = Container()
    with raises(ValueError):
        inst.field_b = b'too_many_bytes'


def test_union_full() -> None:
    class Container(Union):
        data: Bytes[Literal[8]]
        u64: UInt64

    inst = Container(b'\x11\x22\x33\x44\x55\x66\x77\x88')
    assert bytes(inst.data) == b'\x11\x22\x33\x44\x55\x66\x77\x88'

    inst.u64 = 0x0123456789abcdef
    assert bytes(inst.data) == b'\xef\xcd\xab\x89\x67\x45\x23\x01'


def test_union_begin() -> None:
    class Container(Union):
        data: Bytes[Literal[8]]
        u16: UInt16

    inst = Container(b'\x11\x22\x33\x44\x55\x66\x77\x88')
    assert bytes(inst.data) == b'\x11\x22\x33\x44\x55\x66\x77\x88'

    inst.u16 = 0x01234
    assert bytes(inst.data) == b'\x34\x12\x33\x44\x55\x66\x77\x88'


def test_union_end() -> None:
    class TwoInt(Struct):
        field1: UInt16
        field2: UInt16

    class Container(Union):
        data: Bytes[Literal[4]]
        twoint: TwoInt

    inst = Container(b'\x11\x22\x33\x44')
    assert bytes(inst.data) == b'\x11\x22\x33\x44'

    inst.twoint.field2 = 0x1234
    assert bytes(inst.data) == b'\x11\x22\x34\x12'


def test_union_src() -> None:
    class Container(Union):
        data: Bytes[Literal[4]]
        u32: UInt32

    inst = Container(b'\x11\x22\x33\x44')
    assert inst.u32 == 0x44332211

    inst.data[2] = b'\x77'
    assert inst.u32 == 0x44772211


def test_eq() -> None:
    bytes16 = typeof(Bytes(16))
    bytes8 = typeof(Bytes(8))
    bytes16_clone = clone_type(bytes16, name='bytes16')

    assert bytes16 == bytes16  # pylint: disable=comparison-with-itself
    assert bytes16 != bytes8
    assert bytes16 == bytes16_clone

    assert bytes16 != UInt16
    assert bytes16 != Bytes
    assert bytes16 != bytes
