from __future__ import annotations

from struct import Struct as BuiltinStruct
from typing import (Any, Generic, Literal, Optional, Tuple, Type, TypeVar,
                    Union, overload)

from ._base import BaseType, ContainerBase
from ._impl import TypcType, TypcValue
from ._utils import generic_class_getitem

SIZE = TypeVar('SIZE', bound=int)


class Bytes(Generic[SIZE], BaseType):
    @overload
    def __init__(
        self,
        type_or_value: Optional[Union[Literal[0], bytes, Bytes[Any]]] = None,
        value: Literal[None] = None,
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        type_or_value: SIZE,
        value: Optional[Union[Literal[0], bytes, Bytes[Any]]] = None,
    ) -> None:
        ...

    def __init__(self, type_or_value: Any = None, value: Any = None) -> None:
        # pylint: disable=super-init-not-called
        raise NotImplementedError

    @classmethod
    def length(cls) -> int:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    @overload
    def __get__(self, owner: Literal[None],
                inst: Type[ContainerBase]) -> Type[Bytes[SIZE]]:
        ...

    @overload
    def __get__(self, owner: ContainerBase,
                inst: Type[ContainerBase]) -> Bytes[SIZE]:
        ...

    @overload
    def __get__(self, owner: Optional[Any], inst: Type[Any]) -> Bytes[SIZE]:
        ...

    def __get__(
        self,
        owner: Optional[Any],
        inst: Type[Any],
    ) -> Union[Type[Bytes[SIZE]], Bytes[SIZE]]:
        raise NotImplementedError

    @overload
    def __set__(self, owner: ContainerBase, value: Literal[0]) -> None:
        ...

    @overload
    def __set__(self, owner: ContainerBase, value: bytes) -> None:
        ...

    @overload
    def __set__(self: Bytes[SIZE], owner: ContainerBase,
                value: Bytes[int]) -> None:
        ...

    @overload
    def __set__(self: Bytes[SIZE], owner: ContainerBase,
                value: Bytes[SIZE]) -> None:
        ...

    def __set__(self, owner: ContainerBase, value: Any) -> None:
        raise NotImplementedError

    def __getitem__(self, index: int) -> bytes:
        raise NotImplementedError

    def __setitem__(self, index: int, value: bytes) -> None:
        raise NotImplementedError

    def __class_getitem__(cls, size: Any) -> Any:
        # pylint: disable=arguments-differ
        if hasattr(size, '__args__'):
            return BytesType(size.__args__[0], None)
        return generic_class_getitem(cls, size)

    def __bytes__(self) -> bytes:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    def __len__(self) -> int:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    def __typc_set__(self, value: Any) -> None:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    def __new__(  # pylint: disable=arguments-differ
        cls,
        type_or_value: Any = None,
        value: Any = None,
    ):
        if isinstance(type_or_value, int):
            bytes_type = BytesType(type_or_value, None)
            return BytesValue(bytes_type, value)
        raise TypeError


class BytesType(TypcType):
    __slots__ = ()

    def __init__(self, size: int, name: Optional[str]) -> None:
        self.__typc_spec__ = BuiltinStruct(f'{size}s')
        self.__typc_size__ = size
        self.__typc_name__ = name

    def length(self) -> int:
        return self.__typc_size__

    def __call__(
        self,
        values: Union[Literal[None], Literal[0], bytes, BytesValue] = None,
        child_data: Optional[Tuple[TypcValue, int]] = None,
    ) -> BytesValue:
        return BytesValue(self, values, child_data)

    def __typc_get_name__(self) -> str:
        if self.__typc_name__ is None:
            return f'char[{self.__typc_size__}]'
        return self.__typc_name__

    def __typc_clone__(self) -> BytesType:
        new_type: BytesType = BytesType.__new__(BytesType)
        new_type.__typc_spec__ = self.__typc_spec__
        new_type.__typc_size__ = self.__typc_size__
        new_type.__typc_name__ = self.__typc_name__
        return new_type

    def __eq__(self, obj: object) -> bool:
        return (isinstance(obj, BytesType)
                and obj.__typc_size__ == self.__typc_size__)


class BytesValue(TypcValue):
    __slots__ = ('__typc_value__', )
    __typc_type__: BytesType
    __typc_value__: bytes

    def __init__(
        self,
        bytes_type: BytesType,
        values: Union[bytes, BytesValue, Literal[None], Literal[0]] = None,
        child_data: Optional[Tuple[TypcValue, int]] = None,
    ) -> None:
        self.__typc_type__ = bytes_type
        self.__typc_child_data__ = child_data
        size = bytes_type.__typc_size__
        if values in (None, 0):
            values_raw = bytes(size)
        elif isinstance(values, bytes):
            len_values = len(values)
            if len_values == size:
                values_raw = values
            elif len_values < size:
                values_raw = values + bytes(size - len(values))
            else:
                raise ValueError
        elif isinstance(values, BytesValue):
            values_raw = values.__typc_value__
        else:
            raise TypeError
        self.__typc_value__ = values_raw

    def length(self) -> int:
        return self.__typc_type__.__typc_size__

    def __getitem__(self, index: int) -> bytes:
        value = self.__typc_value__
        if index >= len(value):
            raise IndexError
        return value[index:index + 1]

    def __setitem__(self, index: int, value: bytes) -> None:
        prev = self.__typc_value__
        if index >= len(prev):
            raise IndexError
        if len(value) != 1:
            raise ValueError
        self.__typc_value__ = prev[:index] + value + prev[index + 1:]
        if self.__typc_child_data__ is not None:
            parent, self_offset = self.__typc_child_data__
            parent.__typc_changed__(self, value, self_offset + index)

    def __bytes__(self) -> bytes:
        return self.__typc_value__

    def __len__(self) -> int:
        return self.__typc_type__.__typc_size__

    def __typc_set__(self, value: Any) -> None:
        if value in (None, 0):
            self.__typc_value__ = bytes(len(self.__typc_value__))
        elif isinstance(value, bytes):
            size = len(self.__typc_value__)
            len_value = len(value)
            if len_value == size:
                self.__typc_value__ = value
            elif len_value < size:
                self.__typc_value__ = value + bytes(size - len(value))
            else:
                raise ValueError
        elif isinstance(value, BytesValue):
            self.__typc_value__ = value.__typc_value__
        else:
            raise TypeError

    def __typc_set_part__(self, data: bytes, offset: int) -> None:
        prev = self.__typc_value__
        self.__typc_value__ = prev[:offset] + data + prev[offset + len(data):]

    def __typc_changed__(self, source: TypcValue, data: bytes,
                         offset: int) -> None:
        raise NotImplementedError
