from __future__ import annotations

from pytest import raises
from typc import (Padding, Struct, UInt8, UInt16, create_struct, create_union,
                  offsetof, padded, shifted, sizeof, typeof)


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


def test_sizeof() -> None:
    class Pos(Struct):
        x: UInt16
        y: UInt16

    data_t = create_union('Data', {
        'u16': UInt16,
        'pos': Pos,
        'u8': UInt8,
    })

    data = data_t(0)
    assert sizeof(data_t) == 4
    assert sizeof(data) == 4


def test_typeof() -> None:
    data_t = create_union('Data', {
        'u16': UInt16,
        'u8': UInt8,
    })

    data = data_t(0)
    assert typeof(data) is data_t


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


def test_padding() -> None:
    child_t = create_struct('Child', {
        'field1': UInt16,
        'field2': UInt8,
        'field3': UInt8,
    })
    data_t = create_union('Data', {
        'child1': child_t,
        '_pad': Padding(5),
    })
    assert sizeof(data_t) == 5
    data = data_t(b'\x11\x22\x33\x44\x55')
    assert data['child1']['field3'] == 0x44
    assert bytes(data) == b'\x11\x22\x33\x44\x55'


def test_shifted() -> None:
    child1_t = create_struct('Child1', {
        'field1_1': UInt16,
        'field1_2': UInt8,
        'field1_3': UInt8,
    })
    child2_t = create_struct('Child2', {
        'field2_1': UInt8,
        'field2_2': UInt16,
        'field2_3': UInt8,
    })
    data_t = create_union(
        'Data', {
            'child1': child1_t,
            'child2': shifted(child2_t, 1),
            'child3': shifted(UInt16, 1),
        })
    assert sizeof(data_t) == 5
    assert offsetof(data_t, 'child1') == 0
    assert offsetof(data_t, 'child2') == 1
    assert offsetof(data_t, 'child3') == 1

    data = data_t(0)
    child1 = data['child1']
    data['child2']['field2_1'] = 0x12
    assert child1['field1_1'] == 0x1200
    assert data['child3'] == 0x12
    assert bytes(data) == b'\x00\x12\x00\x00\x00'

    child1['field1_2'] = 0x34
    assert data['child2']['field2_2'] == 0x34
    assert data['child3'] == 0x3412
    assert bytes(data) == b'\x00\x12\x34\x00\x00'

    child1['field1_1'] = 0x5678
    assert data['child2']['field2_1'] == 0x56
    assert data['child3'] == 0x3456
    assert bytes(data) == b'\x78\x56\x34\x00\x00'


def test_padded() -> None:
    child_t = create_struct('Child', {
        'field1_1': UInt16,
        'field1_2': UInt16,
    })
    data_t = create_union(
        'Data', {
            'child1': padded(UInt8, 4),
            'child2': padded(UInt16, 1),
            'child3': child_t,
        })

    assert sizeof(data_t) == 5
    assert sizeof(data_t['child1']) == 1
    assert sizeof(data_t['child2']) == 2
    assert sizeof(data_t['child3']) == 4

    data = data_t(0)
    data['child2'] = 0x1234
    assert data['child1'] == 0x34
    assert bytes(data['child3']) == b'\x34\x12\x00\x00'
