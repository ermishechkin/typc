from __future__ import annotations

from typing import (Any, Dict, Generic, Literal, Optional, Tuple, Type,
                    TypeVar, Union, overload)

from ._base import BaseType, ContainerBase
from ._impl import TypcAtomType

SELF = TypeVar('SELF', bound='AtomType[Any]')
CLASS = TypeVar('CLASS')
RES = TypeVar('RES')


class AtomMeta(type):
    def __new__(cls, name: str, bases: Tuple[type, ...],
                namespace_dict: Dict[str, Any]):
        if namespace_dict['__module__'] == __name__:
            return type.__new__(cls, name, bases, namespace_dict)
        return TypcAtomType(namespace_dict['__typc_name__'],
                            namespace_dict['__typc_spec__'],
                            namespace_dict['__typc_size__'],
                            namespace_dict['__typc_native__'])


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
                inst: Type[ContainerBase]) -> SELF:
        ...

    @overload
    def __get__(self, owner: ContainerBase, inst: Type[ContainerBase]) -> RES:
        ...

    @overload
    def __get__(self: SELF, owner: Optional[CLASS], inst: Type[CLASS]) -> SELF:
        ...

    def __get__(self: SELF, owner: Optional[Any],
                inst: Type[Any]) -> Union[SELF, RES]:
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
