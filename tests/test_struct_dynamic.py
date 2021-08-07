from __future__ import annotations

from pytest import raises
from typc import (Padding, UInt8, UInt16, create_struct, offsetof, padded,
                  shifted, sizeof, type_name, typeof)


def test_declaration() -> None:
    pos_t = create_struct('Pos', {
        'x': UInt16,
        'y': UInt16,
    })
    rect_t = create_struct('Rect', {
        'pos': pos_t,
        'width': UInt8,
        'height': UInt8,
    })

    assert rect_t['pos'] is pos_t
    assert rect_t['width'] is UInt8
    assert rect_t['height'] is UInt8


def test_empty() -> None:
    with raises(ValueError):
        _ = create_struct('EmptyStruct', {})


def test_non_type_field() -> None:
    with raises(ValueError):
        _ = create_struct(
            'BadStruct',
            {
                'field': str,  # type: ignore
            })


def test_nonexistent_type_member_get() -> None:
    some_t = create_struct('SomeStruct', {'field': UInt8})

    with raises(KeyError):
        _ = some_t['bad']


def test_nonexistent_value_member_get() -> None:
    some_t = create_struct('SomeStruct', {'field': UInt8})
    some = some_t(0)

    with raises(KeyError):
        _ = some['bad']


def test_nonexistent_value_member_set() -> None:
    some_t = create_struct('SomeStruct', {'field': UInt8})
    some = some_t(0)

    with raises(KeyError):
        some['bad'] = 2


def test_packed_size() -> None:
    some_t = create_struct('SomeStruct', {
        'field1': UInt8,
        'field2': UInt16,
    })
    some = some_t(0)
    assert sizeof(some_t) == 3
    assert sizeof(some) == 3
    assert bytes(some) == b'\x00\x00\x00'


def test_typeof() -> None:
    some_t = create_struct('SomeStruct', {
        'field1': UInt8,
        'field2': UInt16,
    })

    data = some_t(0)
    assert typeof(data) is some_t


def test_offsetof_type() -> None:
    some_t = create_struct('SomeStruct', {
        'field1': UInt8,
        'field2': UInt16,
        'field3': UInt16,
    })

    assert offsetof(some_t, 'field1') == 0
    assert offsetof(some_t, 'field2') == 1
    assert offsetof(some_t, 'field3') == 3
    with raises(KeyError):
        offsetof(some_t, 'bad_field')


def test_offsetof_value() -> None:
    some_t = create_struct('SomeStruct', {
        'field1': UInt8,
        'field2': UInt16,
        'field3': UInt16,
    })

    data = some_t(0)
    assert offsetof(data, 'field1') == 0
    assert offsetof(data, 'field2') == 1
    assert offsetof(data, 'field3') == 3
    with raises(KeyError):
        offsetof(data, 'bad_field')


def test_name() -> None:
    some_t = create_struct('SomeStruct', {
        'field1': UInt8,
        'field2': UInt16,
        'field3': UInt16,
    })

    data = some_t(0)
    assert type_name(some_t) == 'SomeStruct'
    assert type_name(data) == 'SomeStruct'


def test_init_zero() -> None:
    pos_t = create_struct('Pos', {
        'x': UInt16,
        'y': UInt16,
    })
    size_t = create_struct('Size', {
        'width': UInt8,
        'height': UInt8,
    })
    rect_t = create_struct('Rect', {
        'pos': pos_t,
        'size': size_t,
    })

    rect = rect_t(0)
    assert rect['pos']['x'] == 0
    assert rect['pos']['y'] == 0
    assert rect['size']['height'] == 0
    assert rect['size']['width'] == 0

    assert bytes(rect) == b'\x00\x00\x00\x00\x00\x00'


def test_init_tuple() -> None:
    pos_t = create_struct('Pos', {
        'x': UInt16,
        'y': UInt16,
    })
    pos = pos_t((1, 2))
    assert pos['x'] == 1
    assert pos['y'] == 2


def test_init_bytes() -> None:
    pos_t = create_struct('Pos', {
        'x': UInt16,
        'y': UInt16,
    })
    pos = pos_t(b'\x11\x22\x33\x44')
    assert pos['x'] == 0x2211
    assert pos['y'] == 0x4433


def test_init_struct() -> None:
    pos_t = create_struct('Pos', {
        'x': UInt16,
        'y': UInt16,
    })
    pos = pos_t(pos_t((0x1122, 0x3344)))
    assert pos['x'] == 0x1122
    assert pos['y'] == 0x3344


def test_init_bad_type() -> None:
    pos_t = create_struct('Pos', {
        'x': UInt16,
        'y': UInt16,
    })
    with raises(TypeError):
        pos_t('bad value')  # type: ignore


def test_unitialized_member_access() -> None:
    some_t = create_struct('SomeStruct', {
        'field1': UInt16,
        'field2': UInt16,
    })
    inst = some_t()
    assert inst['field2'] == 0


def test_unitialized_member_assignment() -> None:
    some_t = create_struct('SomeStruct', {
        'field1': UInt16,
        'field2': UInt16,
    })
    inst = some_t()
    inst['field2'] = 0x1122
    assert bytes(inst) == b'\x00\x00\x22\x11'


def test_unitialized_convert_to_bytes() -> None:
    pos_t = create_struct('Pos', {
        'x': UInt16,
        'y': UInt16,
    })
    inst = pos_t()
    assert bytes(inst) == b'\x00\x00\x00\x00'


def test_unitialized_substruct_change() -> None:
    child_t = create_struct('Child', {'field': UInt8})
    parent_t = create_struct('Parent', {'child': child_t})
    inst = parent_t()
    inst['child'] = (0x12, )
    assert bytes(inst) == b'\x12'


def test_int_member_assignment() -> None:
    pos_t = create_struct('Pos', {
        'x': UInt16,
        'y': UInt16,
    })
    size_t = create_struct('Size', {
        'width': UInt8,
        'height': UInt8,
    })
    rect_t = create_struct('Rect', {
        'pos': pos_t,
        'size': size_t,
    })
    rect = rect_t(0)
    rect['pos']['y'] = 0x1234
    rect['size']['width'] = 0x56
    assert rect['pos']['x'] == 0
    assert rect['pos']['y'] == 0x1234
    assert rect['size']['height'] == 0
    assert rect['size']['width'] == 0x56
    assert bytes(rect) == b'\x00\x00\x34\x12\x56\x00'


def test_substruct_member_assignment() -> None:
    pos_t = create_struct('Pos', {
        'x': UInt16,
        'y': UInt16,
    })
    size_t = create_struct('Size', {
        'width': UInt8,
        'height': UInt8,
    })
    rect_t = create_struct('Rect', {
        'pos': pos_t,
        'size': size_t,
    })
    rect1 = rect_t(0)
    rect2 = rect_t(0)
    rect1['pos']['x'] = 0x0123
    rect1['pos']['y'] = b'\x67\x45'
    rect1['size']['width'] = UInt8(0x11)
    rect1['size']['height'] = 0x22
    rect2['pos']['x'] = 0x89AB
    rect2['pos']['y'] = 0xCDEF
    rect2['size']['width'] = 0x33
    rect2['size']['height'] = 0x44
    assert bytes(rect1) == b'\x23\x01\x67\x45\x11\x22'
    assert bytes(rect2) == b'\xAB\x89\xEF\xCD\x33\x44'


def test_substruct_assignment() -> None:
    pos_t = create_struct('Pos', {
        'x': UInt16,
        'y': UInt16,
    })
    rect_t = create_struct('Rect', {
        'point1': pos_t,
        'point2': pos_t,
    })

    rect = rect_t((pos_t((0, 0)), pos_t((0, 0))))
    point2_ref = rect['point2']

    rect['point1'] = pos_t((0x0123, 0x4567))
    rect['point2'] = b'\x89\xab\xcd\xef'

    assert rect['point1']['x'] == 0x0123
    assert rect['point1']['y'] == 0x4567
    assert point2_ref['x'] == 0xab89
    assert point2_ref['y'] == 0xefcd

    rect['point2'] = (0x1122, 0x3344)
    assert point2_ref['x'] == 0x1122
    assert point2_ref['y'] == 0x3344

    rect['point2'] = 0
    assert point2_ref['x'] == 0
    assert point2_ref['y'] == 0

    with raises(TypeError):
        rect['point2'] = 'bad value'


def test_multilevel_assignment() -> None:
    child_t = create_struct('Child', {
        'a': UInt8,
        'b': UInt8,
    })
    intermediate_t = create_struct('Intermediate', {
        'child1': child_t(),
        'child2': child_t(),
    })

    parent_t = create_struct('Parent', {
        'field1': intermediate_t,
        'field2': intermediate_t,
    })
    inst = parent_t(b'\x00\x11\x22\x33\x44\x55\x66\x77')
    child1_2 = inst['field1']['child2']
    inst['field1'] = (child_t((1, 2)), child_t((3, 4)))
    assert child1_2['a'] == 3
    assert child1_2['b'] == 4


def test_padding() -> None:
    struct_t = create_struct(
        'SomeStruct', {
            '_pad1': Padding(2),
            'field1': UInt8,
            'field2': UInt16,
            '_pad2': Padding(1),
            '_pad3': Padding(1),
            'field3': UInt16,
            '_pad4': Padding(2),
        })

    assert sizeof(struct_t) == 11
    assert offsetof(struct_t, 'field1') == 2
    assert offsetof(struct_t, 'field2') == 3
    assert offsetof(struct_t, 'field3') == 7

    data = struct_t((0x12, 0x3456, 0x789a))
    assert bytes(data) == b'\x00\x00\x12\x56\x34\x00\x00\x9a\x78\x00\x00'


def test_shifted() -> None:
    struct_t = create_struct(
        'SomeStruct', {
            'field1': shifted(UInt8, 1),
            'field2': UInt16,
            'field3': shifted(UInt16, 3),
        })

    assert sizeof(struct_t) == 9
    assert sizeof(struct_t['field1']) == 1
    assert sizeof(struct_t['field2']) == 2
    assert sizeof(struct_t['field3']) == 2
    assert offsetof(struct_t, 'field1') == 1
    assert offsetof(struct_t, 'field2') == 2
    assert offsetof(struct_t, 'field3') == 7

    data = struct_t((0x12, 0x3456, 0x789a))
    assert bytes(data) == b'\x00\x12\x56\x34\x00\x00\x00\x9a\x78'


def test_padded() -> None:
    struct_t = create_struct(
        'SomeStruct', {
            'field1': padded(UInt8, 2),
            'field2': UInt16,
            'field3': padded(UInt16, 3),
        })
    assert sizeof(struct_t) == 10
    assert sizeof(struct_t['field1']) == 1
    assert sizeof(struct_t['field2']) == 2
    assert sizeof(struct_t['field3']) == 2
    assert offsetof(struct_t, 'field1') == 0
    assert offsetof(struct_t, 'field2') == 3
    assert offsetof(struct_t, 'field3') == 5

    data = struct_t((0x12, 0x3456, 0x789a))
    assert bytes(data) == b'\x12\x00\x00\x56\x34\x9a\x78\x00\x00\x00'


def test_modifiers_classvar() -> None:
    struct_t = create_struct(
        'SomeStruct', {
            'field1': padded(shifted(UInt8, 2), 2),
            '_pad': Padding(1),
            'field2': shifted(UInt16, 2),
            'field3': UInt16(),
        })
    assert sizeof(struct_t) == 12
    assert sizeof(struct_t['field1']) == 1
    assert sizeof(struct_t['field2']) == 2
    assert sizeof(struct_t['field3']) == 2
    assert offsetof(struct_t, 'field1') == 2
    assert offsetof(struct_t, 'field2') == 8
    assert offsetof(struct_t, 'field3') == 10

    data = struct_t((0x12, 0x3456, 0x789a))
    assert bytes(data) == b'\x00\x00\x12\x00\x00\x00\x00\x00\x56\x34\x9a\x78'
