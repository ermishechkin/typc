from __future__ import annotations

from struct import Struct as BuiltinStruct
from typing import (Any, Generic, List, Literal, Optional, Tuple, Type,
                    TypeVar, Union, cast, overload)

from ._base import BaseType, ContainerBase
from ._impl import TypcAtomType, TypcType, TypcValue
from ._utils import generic_class_getitem
from .structure import spec_from_fields

EL = TypeVar('EL', bound=BaseType)
SIZE = TypeVar('SIZE', bound=int)


class Array(Generic[EL, SIZE], BaseType):
    @overload
    def __init__(self,
                 typ: Type[EL],
                 size: SIZE,
                 values: Literal[None] = None) -> None:
        ...

    @overload
    def __init__(self, typ: Type[EL], size: SIZE, values: Literal[0]) -> None:
        ...

    @overload
    def __init__(self, typ: Type[EL], size: SIZE, values: bytes) -> None:
        ...

    @overload
    def __init__(
        self,
        typ: Type[EL],
        size: SIZE,
        values: Tuple[Any, ...],
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        typ: Type[EL],
        size: SIZE,
        values: Array[EL, Any],
    ) -> None:
        ...

    def __init__(
        self,
        typ: Type[EL],
        size: SIZE,
        values: Union[bytes, Tuple[Any, ...], Literal[None], Array[EL, Any],
                      Literal[0]] = None,
    ) -> None:
        # pylint: disable=super-init-not-called
        raise NotImplementedError

    @overload
    def __get__(self, owner: Literal[None],
                inst: Type[ContainerBase]) -> Type[Array[EL, SIZE]]:
        ...

    @overload
    def __get__(self, owner: ContainerBase,
                inst: Type[ContainerBase]) -> Array[EL, SIZE]:
        ...

    @overload
    def __get__(self, owner: Optional[Any],
                inst: Type[Any]) -> Array[EL, SIZE]:
        ...

    def __get__(
        self,
        owner: Optional[Any],
        inst: Type[Any],
    ) -> Union[Type[Array[EL, SIZE]], Array[EL, SIZE]]:
        raise NotImplementedError

    @overload
    def __set__(self, owner: ContainerBase, value: Literal[0]) -> None:
        ...

    @overload
    def __set__(self, owner: ContainerBase, value: Tuple[Any, ...]) -> None:
        ...

    @overload
    def __set__(self, owner: ContainerBase, value: bytes) -> None:
        ...

    @overload
    def __set__(self: Array[EL, SIZE], owner: ContainerBase,
                value: Array[EL, int]) -> None:
        ...

    @overload
    def __set__(self: Array[EL, SIZE], owner: ContainerBase,
                value: Array[EL, SIZE]) -> None:
        ...

    def __set__(self, owner: ContainerBase, value: Any) -> None:
        raise NotImplementedError

    def __getitem__(self, index: int) -> EL:
        raise NotImplementedError

    def __setitem__(
        self,
        index: int,
        value: Union[Tuple[Any, ...], bytes, EL, Literal[0], Any],
    ) -> None:
        raise NotImplementedError

    def __class_getitem__(cls, args: Tuple[Any, ...]) -> Any:
        # pylint: disable=arguments-differ
        el_type, size_literal = args
        if isinstance(el_type, TypcType) and hasattr(size_literal, '__args__'):
            size = size_literal.__args__[0]
            if isinstance(size, int):
                return ArrayType(el_type, size)
        return generic_class_getitem(cls, args)

    def __bytes__(self) -> bytes:
        raise NotImplementedError

    def __typc_set__(self, value: Any) -> None:
        raise NotImplementedError

    def __new__(
        cls,
        element_type: Type[EL],
        size: SIZE,
        values: Any = None,
    ) -> Array[EL, SIZE]:
        # pylint: disable=arguments-differ
        array_type = ArrayType(cast(TypcType, element_type), size)
        array_value = ArrayValue(array_type, values)
        return cast(Array[EL, SIZE], array_value)


class ArrayType(TypcType):
    __slots__ = ('__typc_element__', '__typc_count__')

    def __init__(self, element_type: TypcType, size: int) -> None:
        self.__typc_element__ = element_type
        self.__typc_count__ = size
        spec, arr_size = spec_from_fields((element_type, ))
        self.__typc_spec__ = BuiltinStruct('<' + spec * size)
        self.__typc_size__ = arr_size * size

    def __call__(
        self,
        values: Union[Literal[None], Literal[0], bytes, Tuple[Any, ...],
                      ArrayValue] = None,
    ) -> ArrayValue:
        return ArrayValue(self, values)


class ArrayValue(TypcValue):
    __slots__ = ('__typc_inited__', '__typc_value__')
    __typc_type__: ArrayType
    __typc_value__: List[Any]

    def __init__(
        self,
        array_type: ArrayType,
        values: Union[bytes, Tuple[Any, ...], ArrayValue, Literal[None],
                      Literal[0]] = None,
    ) -> None:
        self.__typc_type__ = array_type
        if values in (None, 0):
            self.__typc_inited__ = False
            return
        if isinstance(values, bytes):
            values_tuple = array_type.__typc_spec__.unpack(values)
        elif isinstance(values, ArrayValue):
            values_tuple = array_type.__typc_spec__.unpack(bytes(values))
        elif isinstance(values, tuple):
            values_tuple = values
        else:
            raise TypeError
        element_type = array_type.__typc_element__
        self.__typc_value__ = [element_type(val) for val in values_tuple]
        self.__typc_inited__ = True

    def __getitem__(self, index: int) -> Union[TypcValue, Any]:
        if not self.__typc_inited__:
            self._zero_init()
        return self.__typc_value__[index]

    def __setitem__(self, index: int, value: Any) -> None:
        if not self.__typc_inited__:
            self._zero_init()
        el_type = self.__typc_type__.__typc_element__
        if isinstance(el_type, TypcAtomType):
            self.__typc_value__[index] = el_type(value)
        else:
            self.__typc_value__[index].__typc_set__(value)

    def _zero_init(self) -> None:
        element_type = self.__typc_type__.__typc_element__
        element_count = self.__typc_type__.__typc_count__
        self.__typc_value__ = [element_type(0) for _ in range(element_count)]
        self.__typc_inited__ = True

    def __bytes__(self) -> bytes:
        if not self.__typc_inited__:
            self._zero_init()
        raw_value: List[Any] = []
        for value in self.__typc_value__:
            if isinstance(value, TypcValue):
                raw_value.append(bytes(value))
            else:
                raw_value.append(value)
        return self.__typc_type__.__typc_spec__.pack(*raw_value)

    def __typc_set__(self, value: Any) -> None:
        if not self.__typc_inited__:
            self.__init__(self.__typc_type__, value)  # type: ignore
            return
        self_type = self.__typc_type__
        new_values: Tuple[Any, ...]
        if value in (None, 0):
            new_values = (0, ) * self_type.__typc_count__
        elif isinstance(value, bytes):
            new_values = self_type.__typc_spec__.unpack(value)
        elif isinstance(value, ArrayValue):
            new_values = self_type.__typc_spec__.unpack(bytes(value))
        elif isinstance(value, tuple):
            new_values = value
        else:
            raise TypeError
        el_type = self_type.__typc_element__
        values_list = self.__typc_value__
        for i, new_val in enumerate(new_values):
            if isinstance(el_type, TypcAtomType):
                values_list[i] = el_type(new_val)
            else:
                values_list[i].__typc_set__(new_val)