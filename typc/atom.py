from __future__ import annotations

from typing import (Any, Dict, Generic, Literal, Optional, Tuple, Type,
                    TypeVar, Union, overload)

from ._base import BaseType, ContainerBase
from ._impl import TypcAtomBase

SELF = TypeVar('SELF', bound='AtomType[Any]')
CLASS = TypeVar('CLASS')
RES = TypeVar('RES')


class AtomMeta(type):
    def __new__(
        cls,
        name: str,
        bases: Tuple[type, ...],
        namespace_dict: Dict[str, Any],
        *,
        native_type: Optional[type] = None,
    ):
        if native_type is not None:
            return type(name, (TypcAtomBase, ),
                        namespace_dict,
                        native_type=native_type)
        return type.__new__(cls, name, bases, namespace_dict)


class AtomType(BaseType, Generic[RES], metaclass=AtomMeta):
    __typc_spec__: str
    __typc_size__: int
    __typc_native__: type

    @overload
    def __init__(self, values: Literal[None] = None) -> None:
        ...

    @overload
    def __init__(self, values: Literal[0]) -> None:
        ...

    @overload
    def __init__(self: SELF, values: SELF) -> None:
        ...

    @overload
    def __init__(self, values: bytes) -> None:
        ...

    @overload
    def __init__(self, values: RES) -> None:
        ...

    def __init__(self, values: Any = None) -> None:
        # pylint: disable=super-init-not-called
        raise NotImplementedError

    @overload
    def __get__(self: SELF, owner: Literal[None],
                inst: Type[ContainerBase]) -> Type[SELF]:
        ...

    @overload
    def __get__(self: SELF, owner: ContainerBase,
                inst: Type[ContainerBase]) -> SELF:
        ...

    @overload
    def __get__(self: SELF, owner: Optional[CLASS], inst: Type[CLASS]) -> SELF:
        ...

    def __get__(self: SELF, owner: Optional[Any],
                inst: Type[Any]) -> Union[Type[SELF], SELF]:
        raise NotImplementedError

    @overload
    def __set__(self, owner: ContainerBase, value: Literal[0]) -> None:
        ...

    @overload
    def __set__(self: SELF, owner: ContainerBase, value: SELF) -> None:
        ...

    @overload
    def __set__(self, owner: ContainerBase, value: bytes) -> None:
        ...

    @overload
    def __set__(self, owner: ContainerBase, value: RES) -> None:
        ...

    def __set__(self, owner: ContainerBase, value: Any) -> None:
        raise NotImplementedError

    def __typc_set__(self, value: Any) -> None:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    def __bytes__(self) -> bytes:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError


@overload
def binary_method(_self: Any, _obj: Union[int, AtomType[int]]) -> int:
    ...


@overload
def binary_method(_self: Any, _obj: Union[float, AtomType[float]]) -> float:
    ...


def binary_method(_self: Any, _obj: Any) -> Union[int, float]:
    ...


def binary_method_int(
    _self: Any,
    _obj: Union[int, AtomType[int]],
) -> int:
    ...


def binary_method_float(
    _self: Any,
    _obj: Union[int, float, AtomType[int], AtomType[float]],
) -> float:
    ...


def inplace_method(
    _self: SELF,
    _obj: Union[int, AtomType[int], float, AtomType[float]],
) -> SELF:
    ...


def inplace_method_int(_self: SELF, _obj: Union[int, AtomType[int]]) -> SELF:
    ...


def cmp_method(_self: Any, _obj: Any) -> bool:
    ...


@overload
def divmod_method(
    _self: Any,
    _obj: Union[int, AtomType[int]],
) -> Tuple[int, int]:
    ...


@overload
def divmod_method(
    _self: Any,
    _obj: Union[float, AtomType[float]],
) -> Tuple[float, float]:
    ...


def divmod_method(_self: Any, _obj: Any) -> Any:
    ...


def divmod_method_float(
    _self: Any,
    _obj: Union[int, float, AtomType[int], AtomType[float]],
) -> Tuple[float, float]:
    ...


class Integer(AtomType[int], native_type=int):
    def __index__(self) -> int:
        ...

    def __abs__(self) -> int:
        ...

    def __bool__(self) -> bool:
        ...

    def __ceil__(self) -> int:
        ...

    def __float__(self) -> float:
        ...

    def __floor__(self) -> int:
        ...

    def __int__(self) -> int:
        ...

    def __invert__(self) -> int:
        ...

    def __neg__(self) -> int:
        ...

    def __pos__(self) -> int:
        ...

    def __round__(self) -> int:
        ...

    def __trunc__(self) -> int:
        ...

    __add__ = binary_method
    __and__ = binary_method_int
    __divmod__ = divmod_method
    __floordiv__ = binary_method
    __lshift__ = binary_method_int
    __mod__ = binary_method
    __mul__ = binary_method
    __or__ = binary_method_int
    __pow__ = binary_method
    __rshift__ = binary_method_int
    __sub__ = binary_method
    __truediv__ = binary_method
    __xor__ = binary_method_int

    __radd__ = binary_method
    __rand__ = binary_method_int
    __rdivmod__ = divmod_method
    __rfloordiv__ = binary_method
    __rlshift__ = binary_method_int
    __rmod__ = binary_method
    __rmul__ = binary_method
    __ror__ = binary_method_int
    __rpow__ = binary_method
    __rrshift__ = binary_method_int
    __rsub__ = binary_method
    __rtruediv__ = binary_method
    __rxor__ = binary_method_int

    __ge__ = cmp_method
    __gt__ = cmp_method
    __le__ = cmp_method
    __lt__ = cmp_method

    __iadd__ = inplace_method
    __iand__ = inplace_method_int
    __ifloordiv__ = inplace_method
    __ilshift__ = inplace_method_int
    __imod__ = inplace_method
    __imul__ = inplace_method
    __ior__ = inplace_method_int
    __ipow__ = inplace_method
    __irshift__ = inplace_method_int
    __isub__ = inplace_method
    __itruediv__ = inplace_method
    __ixor__ = inplace_method_int


class Real(AtomType[float], native_type=float):
    def __abs__(self) -> float:
        ...

    def __bool__(self) -> bool:
        ...

    def __float__(self) -> float:
        ...

    def __int__(self) -> int:
        ...

    def __neg__(self) -> float:
        ...

    def __pos__(self) -> float:
        ...

    def __round__(self) -> int:
        ...

    def __trunc__(self) -> int:
        ...

    __add__ = binary_method_float
    __divmod__ = divmod_method_float
    __floordiv__ = binary_method_float
    __mod__ = binary_method_float
    __mul__ = binary_method_float
    __sub__ = binary_method_float
    __truediv__ = binary_method_float

    __radd__ = binary_method_float
    __rdivmod__ = divmod_method_float
    __rfloordiv__ = binary_method_float
    __rmod__ = binary_method_float
    __rmul__ = binary_method_float
    __rsub__ = binary_method_float
    __rtruediv__ = binary_method_float

    __ge__ = cmp_method
    __gt__ = cmp_method
    __le__ = cmp_method
    __lt__ = cmp_method

    __iadd__ = inplace_method
    __ifloordiv__ = inplace_method
    __imod__ = inplace_method
    __imul__ = inplace_method
    __isub__ = inplace_method
    __itruediv__ = inplace_method
