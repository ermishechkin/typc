from __future__ import annotations

from typing import Any, Type, TypeVar, Union, cast

from ._base import BaseType
from ._impl import TypcType, TypcValue
from .structure import (Struct, StructType, StructValue, UntypedStructType,
                        UntypedStructValue)
from .union import Union as UnionT
from .union import UnionType, UnionValue, UntypedUnionType, UntypedUnionValue

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


def offsetof(
    obj: Union[Struct, Type[Struct], UntypedStructType, UntypedStructValue,
               UnionT, Type[UnionT], UntypedUnionType, UntypedUnionValue],
    field: str,
) -> int:
    obj_: Any = obj
    if isinstance(obj_, (StructValue, UnionValue)):
        return obj_.__typc_type__.__typc_members__[field][0]
    if isinstance(obj_, (StructType, UnionType)):
        return obj_.__typc_members__[field][0]
    raise TypeError(f'{obj!r} is not struct/union type/value')
