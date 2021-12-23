from __future__ import annotations

from struct import Struct as BuiltinStruct
from typing import Any, Literal, Optional, Tuple, Union

from ._utils import false_isinstance, false_issubclass


class TypcType:
    __slots__ = ('__typc_size__', '__typc_spec__', '__typc_name__')
    __typc_spec__: BuiltinStruct
    __typc_size__: int
    __typc_name__: Optional[str]

    def __call__(
        self,
        values: Union[Literal[None], Literal[0], bytes] = None,
        child_data: Optional[Tuple[TypcValue, int]] = None,
    ) -> TypcValue:
        raise NotImplementedError

    def __typc_get_name__(self) -> str:
        raise NotImplementedError

    def __typc_clone__(self) -> TypcType:
        raise NotImplementedError

    def __eq__(self, obj: object) -> bool:
        raise NotImplementedError

    def __instancecheck__(self, instance: Any) -> bool:
        raise NotImplementedError

    def __subclasscheck__(self, subclass: Any) -> bool:
        raise NotImplementedError


class TypcValue:
    __slots__ = ('__typc_type__', '__typc_child_data__')
    __typc_type__: TypcType
    __typc_child_data__: Optional[Tuple[TypcValue, int]]

    def __typc_set__(self, value: Any) -> None:
        raise NotImplementedError

    def __typc_set_part__(self, data: bytes, offset: int) -> None:
        raise NotImplementedError

    def __typc_changed__(self, source: TypcValue, data: bytes,
                         offset: int) -> None:
        raise NotImplementedError

    def __bytes__(self) -> bytes:
        raise NotImplementedError


class TypcAtomType(TypcType):
    __slots__ = ('__typc_native__', )
    __typc_native__: type
    __typc_name__: str

    def __init__(self, name: str, spec: str, size: int,
                 native_type: type) -> None:
        self.__typc_spec__ = BuiltinStruct(spec)
        self.__typc_size__ = size
        self.__typc_name__ = name
        self.__typc_native__ = native_type

    def __call__(
        self,
        values: Any = None,
        child_data: Optional[Tuple[TypcValue, int]] = None,
    ) -> TypcAtomValue:
        return TypcAtomValue(self, values, child_data)

    def __typc_get_name__(self) -> str:
        return self.__typc_name__

    def __typc_clone__(self) -> TypcAtomType:
        new_type: TypcAtomType = TypcAtomType.__new__(TypcAtomType)
        new_type.__typc_spec__ = self.__typc_spec__
        new_type.__typc_size__ = self.__typc_size__
        new_type.__typc_name__ = self.__typc_name__
        new_type.__typc_native__ = self.__typc_native__
        return new_type

    def __eq__(self, obj: object) -> bool:
        return (isinstance(obj, TypcAtomType)
                and obj.__typc_spec__.format == self.__typc_spec__.format)

    def __instancecheck__(self, instance: Any) -> bool:
        if isinstance(instance, TypcAtomValue):
            return instance.__typc_type__ == self
        return false_isinstance(instance)

    def __subclasscheck__(self, subclass: Any) -> bool:
        if isinstance(subclass, TypcAtomType):
            return subclass == self
        return false_issubclass(subclass)


class TypcAtomValue(TypcValue):
    __slots__ = ('__typc_value__', )
    __typc_type__: TypcAtomType
    __typc_value__: Any

    def __init__(
        self,
        atom_type: TypcAtomType,
        value: Union[bytes, TypcAtomValue, Literal[None], Literal[0]] = None,
        child_data: Optional[Tuple[TypcValue, int]] = None,
    ) -> None:
        self.__typc_type__ = atom_type
        self.__typc_child_data__ = child_data
        native_type = atom_type.__typc_native__
        if isinstance(value, native_type):
            value_raw = value
        elif value in (None, 0):
            value_raw = native_type()
        elif isinstance(value, bytes):
            type_size = atom_type.__typc_size__
            value_size = len(value)
            if value_size == type_size:
                value_raw, = atom_type.__typc_spec__.unpack(value)
            else:
                raise ValueError
        elif isinstance(value, TypcAtomValue):
            value_raw = value.__typc_value__
        else:
            raise TypeError
        self.__typc_value__ = value_raw

    def __bytes__(self) -> bytes:
        return self.__typc_type__.__typc_spec__.pack(self.__typc_value__)

    def __typc_set__(self, value: Any) -> None:
        native_type = self.__typc_type__.__typc_native__
        if isinstance(value, native_type):
            self.__typc_value__ = value
        elif value in (None, 0):
            self.__typc_value__ = native_type()
        elif isinstance(value, bytes):
            atom_type = self.__typc_type__
            type_size = atom_type.__typc_size__
            value_size = len(value)
            if value_size == type_size:
                self.__typc_value__, = atom_type.__typc_spec__.unpack(value)
            else:
                raise ValueError
        elif isinstance(value, TypcAtomValue):
            self.__typc_value__ = value.__typc_value__
        else:
            raise TypeError

    def __typc_set_part__(self, data: bytes, offset: int) -> None:
        spec = self.__typc_type__.__typc_spec__
        src_data = spec.pack(self.__typc_value__)
        dst_data = src_data[:offset] + data + src_data[offset + len(data):]
        self.__typc_value__, = spec.unpack(dst_data)

    def __typc_changed__(self, source: TypcValue, data: bytes,
                         offset: int) -> None:
        raise NotImplementedError

    def __eq__(self, obj: Any) -> bool:
        return self.__typc_value__ == obj
