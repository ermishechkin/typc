from __future__ import annotations

from struct import Struct as BuiltinStruct
from typing import (Any, Dict, Generic, List, Literal, Optional, Tuple, Type,
                    TypeVar, Union, overload)

from ._base import BaseType, ContainerBase
from ._impl import TypcAtomValue, TypcType, TypcValue
from ._utils import false_isinstance, false_issubclass, generic_class_getitem
from .structure import field_to_spec

EL = TypeVar('EL', bound=BaseType)
SIZE = TypeVar('SIZE', bound=int)


class ArrayMeta(type):
    def __new__(cls, _name: str, _bases: Tuple[type, ...],
                _namespace_dict: Dict[str, Any]):
        return ArrayBase[Any, Any]()


class ArrayBase(Generic[EL, SIZE]):
    __slots__ = ()

    def __call__(
        self,
        element_type: Any,
        size: Any,
        values: Any = None,
    ) -> ArrayValue:
        if isinstance(element_type, TypcType) and isinstance(size, int):
            array_type = ArrayType(element_type, size, None)
            return ArrayValue(array_type, values)
        raise TypeError

    def __getitem__(self, args: Tuple[Any, ...]) -> Any:
        el_type, size_literal = args
        if isinstance(el_type, TypcType) and hasattr(size_literal, '__args__'):
            size = size_literal.__args__[0]
            if isinstance(size, int):
                return ArrayType(el_type, size, None)
        return generic_class_getitem(self, args)

    def __subclasscheck__(self, subclass: Any) -> bool:
        # pylint: disable=unidiomatic-typecheck
        if type(subclass) is ArrayType or subclass is self:
            return True
        return false_issubclass(subclass)

    def __instancecheck__(self, instance: Any) -> bool:
        # pylint: disable=unidiomatic-typecheck
        if type(instance) is ArrayValue:
            return True
        return false_isinstance(instance)


class Array(Generic[EL, SIZE], BaseType, metaclass=ArrayMeta):
    @overload
    def __init__(
        self,
        type_or_value: Type[EL],
        size: SIZE,
        values: Union[Literal[0], Literal[None], bytes, Tuple[Any, ...],
                      Array[EL, Any]] = None,
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        type_or_value: Union[Literal[0], Literal[None], bytes, Tuple[Any, ...],
                             Array[EL, Any]] = None,
        size: Literal[None] = None,
        values: Literal[None] = None,
    ) -> None:
        ...

    def __init__(
        self,
        type_or_value: Any = None,
        size: Optional[SIZE] = None,
        values: Any = None,
    ) -> None:
        # pylint: disable=super-init-not-called
        raise NotImplementedError

    @classmethod
    def item_type(cls: Type[Array[EL, SIZE]]) -> Type[EL]:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    @classmethod
    def length(cls) -> int:
        ...  # mark as non-abstract for pylint
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

    def __bytes__(self) -> bytes:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    def __len__(self) -> int:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    def __typc_set__(self, value: Any) -> None:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError


class ArrayType(TypcType):
    __slots__ = ('__typc_element__', '__typc_count__')

    def __init__(self, element_type: TypcType, size: int,
                 name: Optional[str]) -> None:
        self.__typc_element__ = element_type
        self.__typc_count__ = size
        spec = field_to_spec(element_type)
        self.__typc_spec__ = BuiltinStruct('<' + spec * size)
        self.__typc_size__ = self.__typc_spec__.size
        self.__typc_name__ = name

    def item_type(self) -> TypcType:
        return self.__typc_element__

    def length(self) -> int:
        return self.__typc_count__

    def __call__(
        self,
        values: Union[Literal[None], Literal[0], bytes, Tuple[Any, ...],
                      ArrayValue] = None,
        child_data: Optional[Tuple[TypcValue, int]] = None,
    ) -> ArrayValue:
        return ArrayValue(self, values, child_data)

    def __typc_get_name__(self) -> str:
        if self.__typc_name__ is None:
            el_type_name = self.__typc_element__.__typc_get_name__()
            el_count = self.__typc_count__
            return f'{el_type_name}[{el_count}]'
        return self.__typc_name__

    def __typc_clone__(self) -> ArrayType:
        new_type: ArrayType = ArrayType.__new__(ArrayType)
        new_type.__typc_spec__ = self.__typc_spec__
        new_type.__typc_size__ = self.__typc_size__
        new_type.__typc_name__ = self.__typc_name__
        new_type.__typc_element__ = self.__typc_element__
        new_type.__typc_count__ = self.__typc_count__
        return new_type

    def __eq__(self, obj: object) -> bool:
        if obj is self:
            return True
        return (isinstance(obj, ArrayType)
                and obj.__typc_count__ == self.__typc_count__
                and obj.__typc_element__ == self.__typc_element__)

    def __instancecheck__(self, instance: Any) -> bool:
        if isinstance(instance, ArrayValue):
            return instance.__typc_type__ == self
        return false_isinstance(instance)

    def __subclasscheck__(self, subclass: Any) -> bool:
        if isinstance(subclass, ArrayType):
            return subclass == self
        if subclass is Array:
            return False
        return false_issubclass(subclass)


class ArrayValue(TypcValue):
    __slots__ = ('__typc_inited__', '__typc_value__')
    __typc_type__: ArrayType
    __typc_value__: List[TypcValue]

    def __init__(
        self,
        array_type: ArrayType,
        values: Union[bytes, Tuple[Any, ...], ArrayValue, Literal[None],
                      Literal[0]] = None,
        child_data: Optional[Tuple[TypcValue, int]] = None,
    ) -> None:
        self.__typc_type__ = array_type
        self.__typc_child_data__ = child_data
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
        element_size = element_type.__typc_size__
        self.__typc_value__ = [
            element_type(
                val,
                None if child_data is None else
                (self, child_data[1] + idx * element_size),
            ) for idx, val in enumerate(values_tuple)
        ]
        self.__typc_inited__ = True

    def item_type(self) -> TypcType:
        return self.__typc_type__.__typc_element__

    def length(self) -> int:
        return self.__typc_type__.__typc_count__

    def __getitem__(self, index: int) -> TypcValue:
        if not self.__typc_inited__:
            self._zero_init()
        return self.__typc_value__[index]

    def __setitem__(self, index: int, value: Any) -> None:
        if not self.__typc_inited__:
            self._zero_init()
        el_type = self.__typc_type__.__typc_element__
        self.__typc_value__[index].__typc_set__(value)
        if self.__typc_child_data__ is not None:
            parent, self_offset = self.__typc_child_data__
            parent.__typc_changed__(
                self, bytes(self.__typc_value__[index]),
                self_offset + index * el_type.__typc_size__)

    def _zero_init(self) -> None:
        element_type = self.__typc_type__.__typc_element__
        element_count = self.__typc_type__.__typc_count__
        element_size = element_type.__typc_size__
        child_data = self.__typc_child_data__
        self.__typc_value__ = [
            element_type(
                0,
                None if child_data is None else
                (self, child_data[1] + idx * element_size),
            ) for idx in range(element_count)
        ]
        self.__typc_inited__ = True

    def __bytes__(self) -> bytes:
        if not self.__typc_inited__:
            self._zero_init()
        raw_value = tuple(
            (v.__typc_value__ if isinstance(v, TypcAtomValue) else bytes(v))
            for v in self.__typc_value__)
        return self.__typc_type__.__typc_spec__.pack(*raw_value)

    def __len__(self) -> int:
        return self.__typc_type__.__typc_count__

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
        values_list = self.__typc_value__
        for i, new_val in enumerate(new_values):
            values_list[i].__typc_set__(new_val)

    def __typc_set_part__(self, data: bytes, offset: int) -> None:
        el_type = self.__typc_type__.__typc_element__
        el_size = el_type.__typc_size__
        values_list = self.__typc_value__
        first_off = offset % el_size
        first_idx = offset // el_size
        last_idx = (offset + len(data) - 1) // el_size
        if first_off:
            el_data = data[:el_size - first_off]
            values_list[first_idx].__typc_set_part__(el_data, first_off)
            first_idx += 1
            data = data[el_size - first_off:]
        for idx in range(last_idx - first_idx + 1):
            el_data = data[idx * el_size:(idx + 1) * el_size]
            if len(el_data) == el_size:
                values_list[first_idx + idx].__typc_set__(el_data)
            else:
                values_list[first_idx + idx].__typc_set_part__(el_data, 0)

    def __typc_changed__(self, source: TypcValue, data: bytes,
                         offset: int) -> None:
        assert self.__typc_child_data__ is not None
        parent, _ = self.__typc_child_data__
        parent.__typc_changed__(self, data, offset)
