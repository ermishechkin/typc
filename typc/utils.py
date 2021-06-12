from __future__ import annotations

from typing import Any, Type, TypeVar, Union, cast

from ._base import BaseType
from ._impl import TypcType, TypcValue

TYPE = TypeVar('TYPE', bound=BaseType)


def typeof(obj: TYPE) -> Type[TYPE]:
    obj_: Any = obj
    if isinstance(obj_, TypcValue):
        return cast(Type[TYPE], obj_.__typc_type__)
    raise TypeError(f'{obj!r} is not typc value')


def sizeof(obj: Union[BaseType, Type[BaseType]]) -> int:
    obj_: Any = obj
    if isinstance(obj_, TypcType):
        return obj_.__typc_size__
    if isinstance(obj_, TypcValue):
        return obj_.__typc_type__.__typc_size__
    raise TypeError(f'{obj!r} is not typc type/value')
