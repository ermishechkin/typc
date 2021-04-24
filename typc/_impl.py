from __future__ import annotations

from struct import Struct as BuiltinStruct
from typing import Any, Literal, Union, cast


class TypcType:
    __slots__ = ('__typc_size__', '__typc_spec__')
    __typc_spec__: BuiltinStruct
    __typc_size__: int

    def __call__(
        self,
        values: Union[Literal[None], Literal[0], bytes] = None,
    ) -> TypcValue:
        raise NotImplementedError


class TypcValue:
    __slots__ = ('__typc_type__', )
    __typc_type__: TypcType

    def __typc_set__(self, value: Any) -> None:
        raise NotImplementedError

    def __bytes__(self) -> bytes:
        raise NotImplementedError


class TypcAtomType(TypcType):
    __slots__ = ('__typc_native__', )
    __typc_native__: type

    def __init__(self, spec: str, size: int, native_type: type) -> None:
        self.__typc_spec__ = BuiltinStruct(spec)
        self.__typc_size__ = size
        self.__typc_native__ = native_type

    def __call__(self, values: Any = None) -> Union[TypcValue, Any]:
        if isinstance(values, self.__typc_native__):
            return values
        if values is None:
            return cast(TypcValue, self)
        if values == 0:
            return self.__typc_native__()
        if isinstance(values, bytes):
            return self.__typc_spec__.unpack(values)[0]
        raise TypeError
