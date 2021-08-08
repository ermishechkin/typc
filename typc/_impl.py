from __future__ import annotations

from struct import Struct as BuiltinStruct
from typing import Any, Literal, Optional, Tuple, Union, cast


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
        child_data: Optional[Tuple[TypcValue, int]] = None
    ) -> Union[TypcValue, Any]:
        if isinstance(values, self.__typc_native__):
            return values
        if values is None:
            return cast(TypcValue, self)
        if values == 0:
            return self.__typc_native__()
        if isinstance(values, bytes):
            return self.__typc_spec__.unpack(values)[0]
        raise TypeError

    def __typc_get_name__(self) -> str:
        return self.__typc_name__

    def __typc_clone__(self) -> TypcAtomType:
        new_type: TypcAtomType = TypcAtomType.__new__(TypcAtomType)
        new_type.__typc_spec__ = self.__typc_spec__
        new_type.__typc_size__ = self.__typc_size__
        new_type.__typc_name__ = self.__typc_name__
        new_type.__typc_native__ = self.__typc_native__
        return new_type
