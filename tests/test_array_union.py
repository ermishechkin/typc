from __future__ import annotations

from typing import Literal

from typc import Array, Struct, UInt8, UInt16, UInt32, UInt64, Union


def test_array_as_member_src() -> None:
    class Data(Union):
        u16: UInt16
        a2: Array[UInt8, Literal[2]]
        u8: UInt8

    data = Data()
    data.a2[1] = 0x12
    assert data.u16 == 0x1200
    assert data.u8 == 0


def test_changed_full() -> None:
    class Data(Union):
        u16: UInt16
        a2: Array[UInt8, Literal[2]]

    data = Data()
    array_ref = data.a2

    data.u16 = 0x1234
    assert array_ref[0] == 0x34
    assert array_ref[1] == 0x12


def test_changed_begin() -> None:
    class Data(Union):
        a2: Array[UInt8, Literal[2]]
        ui8: UInt8

    data = Data()
    array_ref = data.a2

    data.ui8 = 0x12
    assert array_ref[0] == 0x12
    assert array_ref[1] == 0


def test_changed_mid() -> None:
    class Data(Union):
        a1: Array[UInt8, Literal[4]]
        a2: Array[UInt8, Literal[4]]

    data = Data()
    array_ref = data.a2

    data.a1[2] = 0x12
    assert array_ref[2] == 0x12
    assert bytes(array_ref) == b'\x00\x00\x12\x00'


def test_changed_end() -> None:
    class Data(Union):
        a1: Array[UInt8, Literal[4]]
        a2: Array[UInt8, Literal[4]]

    data = Data()
    array_ref = data.a2

    data.a1[3] = 0x12
    assert array_ref[3] == 0x12
    assert bytes(array_ref) == b'\x00\x00\x00\x12'


def test_changed_part_begin() -> None:
    class Data(Union):
        a1: Array[UInt8, Literal[4]]
        a2: Array[UInt16, Literal[2]]

    data = Data()
    array_ref = data.a2

    data.a1[0] = 0x12
    assert array_ref[0] == 0x12
    assert bytes(array_ref) == b'\x12\x00\x00\x00'


def test_changed_part_mid_one() -> None:
    class Data(Union):
        a1: Array[UInt8, Literal[8]]
        a2: Array[UInt32, Literal[2]]

    data = Data()
    array_ref = data.a2

    data.a1[6] = 0x12
    assert array_ref[1] == 0x120000
    assert bytes(array_ref) == b'\x00\x00\x00\x00\x00\x00\x12\x00'


def test_changed_part_end() -> None:
    class Data(Union):
        a1: Array[UInt8, Literal[4]]
        a2: Array[UInt16, Literal[2]]

    data = Data()
    array_ref = data.a2

    data.a1[3] = 0x12
    assert array_ref[1] == 0x1200
    assert bytes(array_ref) == b'\x00\x00\x00\x12'


def test_changed_many() -> None:
    class Data(Union):
        a1: Array[UInt8, Literal[12]]
        a2: Array[UInt32, Literal[3]]

    data = Data()
    array_ref = data.a1

    data.a2[1] = 0x12345678
    assert array_ref[4] == 0x78
    assert array_ref[5] == 0x56
    assert array_ref[6] == 0x34
    assert array_ref[7] == 0x12
    assert (bytes(array_ref) ==
            b'\x00\x00\x00\x00\x78\x56\x34\x12\x00\x00\x00\x00')


def test_changed_multilevel_src_1() -> None:
    class Data(Union):
        a1: Array[UInt8, Literal[8]]
        a2: Array[Array[UInt16, Literal[2]], Literal[2]]

    data = Data()
    array_ref = data.a1

    data.a2[1][0] = 0x1234
    assert array_ref[4] == 0x34
    assert array_ref[5] == 0x12


def test_changed_multilevel_src_2() -> None:
    class Data(Union):
        a1: Array[UInt8, Literal[8]]
        a2: Array[Array[UInt16, Literal[2]], Literal[2]]

    data = Data()
    array_ref = data.a1

    data.a2[1] = b'\x12\x34\x56\x78'
    assert array_ref[4] == 0x12
    assert array_ref[5] == 0x34
    assert array_ref[6] == 0x56
    assert array_ref[7] == 0x78


def test_changed_multilevel_dst_one() -> None:
    class Data(Union):
        a1: Array[UInt8, Literal[8]]
        a2: Array[Array[UInt16, Literal[2]], Literal[2]]

    data = Data()
    array_ref = data.a2

    data.a1[7] = 0x12
    assert array_ref[1][1] == 0x1200
    assert bytes(array_ref) == b'\x00\x00\x00\x00\x00\x00\x00\x12'


def test_changed_multilevel_dst_many() -> None:
    class Data(Union):
        a1: Array[UInt64, Literal[2]]
        a2: Array[Array[UInt16, Literal[2]], Literal[4]]

    # 00000000000000001111111111111111 - a1
    # 00000000111111112222222233333333 - a2
    # 00001111000011110000111100001111 - a2[i]

    data = Data(b'\x00\x11\x22\x33\x44\x55\x66\x77' +
                b'\x88\x99\xaa\xbb\xcc\xdd\xee\xff')
    array_ref = data.a2

    data.a1[1] = 0x0123456789abcdef
    assert array_ref[2][0] == 0xcdef
    assert array_ref[2][1] == 0x89ab
    assert array_ref[3][0] == 0x4567
    assert array_ref[3][1] == 0x0123
    assert bytes(array_ref[2]) == b'\xef\xcd\xab\x89'
    assert bytes(array_ref[3]) == b'\x67\x45\x23\x01'


def test_changed_multilevel_dst_many_unaligned() -> None:
    class Data(Union):
        a1: Array[UInt64, Literal[2]]
        a2: Array[Array[UInt16, Literal[3]], Literal[3]]

    # 00000000000000001111111111111111     - a1
    # 000000000000111111111111222222222222 - a2
    # 000011112222000011112222000011112222 - a2[i]

    data = Data(b'\x00\x11\x22\x33\x44\x55' + b'\x66\x77\x88\x99\xaa\xbb' +
                b'\xcc\xdd\xee\xff\x13\x25')
    array_ref = data.a2

    data.a1[1] = 0x0123456789abcdef
    assert array_ref[1][0] == 0x7766
    assert array_ref[1][1] == 0xcdef
    assert array_ref[1][2] == 0x89ab
    assert array_ref[2][0] == 0x4567
    assert array_ref[2][1] == 0x0123
    assert array_ref[2][2] == 0x2513
    assert bytes(array_ref[0]) == b'\x00\x11\x22\x33\x44\x55'
    assert bytes(array_ref[1]) == b'\x66\x77\xef\xcd\xab\x89'
    assert bytes(array_ref[2]) == b'\x67\x45\x23\x01\x13\x25'


def test_shifted_in_union() -> None:
    class Struct1(Struct):
        field1_1: UInt16
        field1_2: UInt16

    class Struct2(Struct):
        field2_1: UInt8
        field2_2: Array[Struct1, Literal[2]]

    class SomeUnion(Union):
        field_s: Struct2
        field_a: Array[UInt8, Literal[9]]

    union = SomeUnion(0)
    union.field_s.field2_2[1].field1_2 = 0x1234

    assert union.field_a[7] == 0x34
    assert union.field_a[8] == 0x12
    assert bytes(union) == b'\x00\x00\x00\x00\x00\x00\x00\x34\x12'
