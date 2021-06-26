from __future__ import annotations

from typing import Any, Generic, Type, TypeVar, overload

from ._base import BaseType
from ._impl import TypcType, TypcValue
from ._modifier import Modified
from ._utils import generic_class_getitem

PADDING = TypeVar('PADDING', bound=int)


class Padding(Generic[PADDING]):
    __typc_padding__: int
    __slots__ = ('__typc_padding__', )

    def __init__(self, size: PADDING) -> None:
        self.__typc_padding__ = size

    def __class_getitem__(cls, size_literal: Any) -> Any:
        # pylint: disable=arguments-differ
        if hasattr(size_literal, '__args__'):
            size = size_literal.__args__[0]
            if isinstance(size, int):
                return Padding(size)
        return generic_class_getitem(cls, size_literal)


class Shift:
    __slots__ = ('__typc_shift__', )

    def __init__(self, shift: int) -> None:
        self.__typc_shift__ = shift


TYP = TypeVar('TYP', bound=BaseType)


@overload
def shifted(typ: TYP, shift: int) -> TYP:
    ...


@overload
def shifted(typ: Type[TYP], shift: int) -> TYP:
    ...


def shifted(typ: Any, shift: int) -> Any:
    if isinstance(typ, TypcType):
        return Modified(typ, shift=shift)
    if isinstance(typ, TypcValue):
        return Modified(typ.__typc_type__, shift=shift)
    if isinstance(typ, Modified):
        typ.__typc_shift__ += shift
        return typ
    raise TypeError


@overload
def padded(typ: TYP, padding: int) -> TYP:
    ...


@overload
def padded(typ: Type[TYP], padding: int) -> TYP:
    ...


def padded(typ: Any, padding: int) -> Any:
    if isinstance(typ, TypcType):
        return Modified(typ, padding=padding)
    if isinstance(typ, TypcValue):
        return Modified(typ.__typc_type__, padding=padding)
    if isinstance(typ, Modified):
        typ.__typc_padding__ += padding
        return typ
    raise TypeError
