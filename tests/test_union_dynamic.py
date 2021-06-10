from __future__ import annotations

from pytest import raises
from typc import Struct, UInt8, UInt16, create_union


def test_declaration() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    data_t = create_union('Data', {
        'u16': UInt16,
        'pos': Pos,
        'u8': UInt8,
    })
    assert data_t['u16'] is UInt16
    assert data_t['pos'] is Pos
    assert data_t['u8'] is UInt8


def test_empty() -> None:
    with raises(ValueError):
        create_union('EmptyUnion', {})


def test_non_type_field_annotation() -> None:
    with raises(ValueError):
        create_union(
            'BadUnion',
            {
                'field': str,  # type: ignore
            })


def test_nonexistent_type_member_get() -> None:
    some_t = create_union('SomeUnion', {'field': UInt8})
    with raises(KeyError):
        _ = some_t['bad']


def test_nonexistent_value_member_get() -> None:
    some_t = create_union('SomeUnion', {'field': UInt8})
    inst = some_t(0)
    with raises(KeyError):
        _ = inst['bad']


def test_nonexistent_value_member_set() -> None:
    some_t = create_union('SomeUnion', {'field': UInt8})
    inst = some_t(0)
    with raises(KeyError):
        inst['bad'] = 1


def test_init_zero() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    data_t = create_union('Data', {
        'u16': UInt16,
        'pos': Pos,
        'u8': UInt8,
    })

    data = data_t(0)
    assert data['pos'].x == 0
    assert data['pos'].y == 0
    assert data['u16'] == 0
    assert data['u8'] == 0
    assert bytes(data) == b'\x00\x00\x00\x00'


def test_init_bytes() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    data_t = create_union('Data', {
        'u16': UInt16,
        'pos': Pos,
        'u8': UInt8,
    })

    data = data_t(b'\x11\x22\x33\x44')
    assert data['u16'] == 0x2211
    assert data['pos'].x == 0x2211
    assert data['pos'].y == 0x4433
    assert data['u8'] == 0x11


def test_init_union() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    data_t = create_union('Data', {
        'u16': UInt16,
        'pos': Pos(),
        'u8': UInt8,
    })

    data1 = data_t(b'\x11\x22\x33\x44')
    data2 = data_t(data1)

    assert data2['u16'] == 0x2211
    assert data2['pos'].x == 0x2211
    assert data2['pos'].y == 0x4433
    assert data2['u8'] == 0x11


def test_init_bad_type() -> None:
    data_t = create_union('Data', {
        'u16': UInt16,
        'u8': UInt8,
    })
    with raises(TypeError):
        data_t('Bad value')  # type: ignore
