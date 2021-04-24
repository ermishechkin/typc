from __future__ import annotations

from typing import Any, Literal, Optional, Type, TypeVar, Union, overload

SELF = TypeVar('SELF', bound='ContainerBase')
CLASS = TypeVar('CLASS')


class BaseType:
    __typc_size__: int
    __typc_spec__: str
    __slots__ = ()

    @overload
    def __init__(self, values: Literal[None] = None) -> None:
        ...

    @overload
    def __init__(self, values: Literal[0]) -> None:
        ...

    @overload
    def __init__(self, values: bytes) -> None:
        ...

    def __init__(self, values: Any = None) -> None:
        raise NotImplementedError

    def __bytes__(self) -> bytes:
        raise NotImplementedError

    def __typc_set__(self, value: Any) -> None:
        raise NotImplementedError


class ContainerBase(BaseType):
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

    def __typc_set__(self, value: Any) -> None:
        raise NotImplementedError
