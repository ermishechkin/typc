from __future__ import annotations

from typing_extensions import Annotated

from pytest import raises
from typc import (Array, Struct, UInt8, UInt16, create_struct, offsetof,
                  padded, shifted, sizeof)


def test_struct_modified_member_classvar() -> None:
    class SomeStruct(Struct):
        field1 = shifted(Array(UInt16, 3), 1)
        field2 = padded(Array(UInt8, 3), 2)

    assert sizeof(SomeStruct) == 12
    assert sizeof(SomeStruct.field1) == 6
    assert sizeof(SomeStruct.field2) == 3
    assert offsetof(SomeStruct, 'field1') == 1
    assert offsetof(SomeStruct, 'field2') == 7

    data = SomeStruct(((0x1122, 0x3344, 0x5566), (0x77, 0x88, 0x99)))
    assert bytes(data) == b'\x00\x22\x11\x44\x33\x66\x55\x77\x88\x99\x00\x00'


def test_struct_modified_member_dynamic() -> None:
    struct_t = create_struct(
        'SomeStruct', {
            'field1': shifted(Array(UInt16, 3), 1),
            'field2': padded(Array(UInt8, 3), 2),
        })
    assert sizeof(struct_t) == 12
    assert sizeof(struct_t['field1']) == 6
    assert sizeof(struct_t['field2']) == 3
    assert offsetof(struct_t, 'field1') == 1
    assert offsetof(struct_t, 'field2') == 7

    data = struct_t(((0x1122, 0x3344, 0x5566), (0x77, 0x88, 0x99)))
    assert bytes(data) == b'\x00\x22\x11\x44\x33\x66\x55\x77\x88\x99\x00\x00'


def test_empty_annotated() -> None:
    class SomeStruct(Struct):
        field1: Annotated[UInt16, '3rd party annotation']
        field2: UInt16

    _ = SomeStruct


def test_padded_bad() -> None:
    with raises(TypeError):

        class SomeStruct(Struct):
            field1 = padded('bad value', 2)  # type: ignore
            field2 = UInt16()

        _ = SomeStruct


def test_shifted_bad() -> None:
    with raises(TypeError):

        class SomeStruct(Struct):
            field1 = shifted('bad value', 2)  # type: ignore
            field2 = UInt16()

        _ = SomeStruct
