from __future__ import annotations

from typing import (Any, Generic, Literal, Optional, Tuple, Type, TypeVar,
                    Union, cast, overload)

from ._base import BaseType, ContainerBase
from ._impl import TypcAtomType, TypcType, TypcValue
from ._utils import generic_class_getitem
from .atom import AtomType
from .atoms import UInt16, UInt32, UInt64

INT = TypeVar('INT', bound=AtomType[int])
REF = TypeVar('REF', bound=Union[BaseType, 'Void', 'ForwardRef'])
REFNOFWD = TypeVar('REFNOFWD', bound=Union[BaseType, 'Void'])
REFX = Union[TypcType, Type['Void']]


class Void:
    pass


class ForwardRef:
    pass


class PointerType(TypcType):
    __slots__ = ('__typc_int_type__', '__typc_ref_type__')

    def __init__(
        self,
        int_type: TypcAtomType,
        ref_type: Optional[REFX],
    ) -> None:
        self.__typc_int_type__ = int_type
        self.__typc_ref_type__ = ref_type
        self.__typc_spec__ = int_type.__typc_spec__
        self.__typc_size__ = int_type.__typc_size__

    def __call__(
        self,
        values: Union[Literal[None], bytes, int, PointerValue] = None,
        child_data: Optional[Tuple[TypcValue, int]] = None,
    ) -> PointerValue:
        return PointerValue(self, values, child_data)

    def __typc_get_name__(self) -> str:
        ref_type = self.__typc_ref_type__
        if isinstance(ref_type, TypcType):
            return f'{ref_type.__typc_get_name__()} *'
        return 'void *'

    def __typc_clone__(self) -> PointerType:
        new_type: PointerType = PointerType.__new__(PointerType)
        new_type.__typc_spec__ = self.__typc_spec__
        new_type.__typc_size__ = self.__typc_size__
        new_type.__typc_int_type__ = self.__typc_int_type__
        new_type.__typc_ref_type__ = self.__typc_ref_type__
        return new_type

    def int_type(self) -> TypcType:
        return self.__typc_int_type__

    def ref_type(self) -> REFX:
        ref_type = self.__typc_ref_type__
        if ref_type is None:
            return Void
        return ref_type

    def set_ref_type(self, new_ref_type: REFX) -> None:
        if self.__typc_ref_type__ is not None:
            raise TypeError('Pointer already has type')
        if not (isinstance(new_ref_type, TypcType) or new_ref_type is Void):
            raise TypeError(f'{new_ref_type!r} is not valid ref type')
        self.__typc_ref_type__ = new_ref_type


class PointerValue(TypcValue):
    __slots__ = ('__typc_value__', )
    __typc_type__: PointerType
    __typc_value__: int

    def __init__(
        self,
        ptr_type: PointerType,
        values: Union[Literal[None], bytes, int, PointerValue] = None,
        child_data: Optional[Tuple[TypcValue, int]] = None,
    ) -> None:
        self.__typc_type__ = ptr_type
        self.__typc_child_data__ = child_data
        self.set(values)

    def int_type(self) -> TypcType:
        return self.__typc_type__.__typc_int_type__

    def ref_type(self) -> REFX:
        return self.__typc_type__.ref_type()

    def __bytes__(self) -> bytes:
        return self.__typc_type__.__typc_spec__.pack(self.__typc_value__)

    def __int__(self) -> int:
        return self.__typc_value__

    def get(self) -> int:
        return self.__typc_value__

    def set(self,
            value: Union[Literal[None], bytes, int,
                         PointerValue] = None) -> None:
        value_: Any = value
        if value_ is None:
            int_value = 0
        elif isinstance(value_, int):
            int_value = value_
        elif isinstance(value_, bytes):
            int_value, = self.__typc_type__.__typc_spec__.unpack(value_)
        elif isinstance(value_, PointerValue):
            int_value = value_.__typc_value__
        else:
            raise TypeError
        self.__typc_value__ = int_value

    def __typc_set__(self, value: Any) -> None:
        self.set(value)

    def __typc_set_part__(self, data: bytes, offset: int) -> None:
        src_data = bytes(self)
        dst_data = src_data[:offset] + data + src_data[offset + len(data):]
        self.__typc_value__, = (
            self.__typc_type__.__typc_spec__.unpack(dst_data))

    def __typc_changed__(self, source: TypcValue, data: bytes,
                         offset: int) -> None:
        raise NotImplementedError


class _Pointer(BaseType, Generic[INT, REF]):
    __typc_int_type__: Type[INT]

    @overload
    def __init__(
        self,
        type_or_value: Optional[Union[int, bytes, _Pointer[INT, REF]]] = None,
        value: Literal[None] = None,
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        type_or_value: Type[REF],
        value: Optional[Union[int, bytes, _Pointer[INT, REF]]] = None,
    ) -> None:
        ...

    def __init__(self, type_or_value: Any = None, value: Any = None) -> None:
        # pylint: disable=super-init-not-called
        raise NotImplementedError

    @overload
    def __get__(self, owner: Literal[None],
                inst: Type[ContainerBase]) -> Type[_Pointer[INT, REF]]:
        ...

    @overload
    def __get__(self, owner: Any, inst: Type[Any]) -> _Pointer[INT, REF]:
        ...

    def __get__(
        self, owner: Optional[Any], inst: Type[Any]
    ) -> Union[_Pointer[INT, REF], Type[_Pointer[INT, REF]]]:
        raise NotImplementedError

    @overload
    def __set__(self, owner: ContainerBase, value: _Pointer[INT, REF]) -> None:
        ...

    @overload
    def __set__(self, owner: ContainerBase, value: bytes) -> None:
        ...

    @overload
    def __set__(self, owner: ContainerBase, value: int) -> None:
        ...

    def __set__(self, owner: ContainerBase, value: Any) -> None:
        raise NotImplementedError

    def __typc_set__(self, value: Any) -> None:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    def __bytes__(self) -> bytes:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    def __int__(self) -> int:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    @classmethod
    def int_type(cls) -> Type[INT]:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    @overload
    @classmethod
    def ref_type(cls: Type[_Pointer[INT, REFNOFWD]]) -> Type[REFNOFWD]:
        ...

    @overload
    @classmethod
    def ref_type(
        cls: Type[_Pointer[INT, ForwardRef]], ) -> Type[Union[BaseType, Void]]:
        ...

    @classmethod
    def ref_type(cls: Any) -> Any:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    @classmethod
    def set_ref_type(cls: Type[_Pointer[INT, ForwardRef]],
                     new_ref_type: Type[Union[BaseType, Void]]) -> None:
        # pylint: disable=no-self-use,unused-argument
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    def get(self) -> int:
        # pylint: disable=no-self-use
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    def set(
        self,
        value: Union[bytes, int, _Pointer[INT, REF]],
    ) -> None:
        # pylint: disable=no-self-use,unused-argument
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    def __class_getitem__(cls, args: Tuple[Any, ...]) -> Any:
        # pylint: disable=arguments-differ
        int_type = args[0]
        assert isinstance(int_type, TypcAtomType)

        # Do not specify type args for _Pointer to avoid recursion
        class PointerSized(_Pointer):  # type: ignore
            __typc_int_type__ = cast(Type[INT], int_type)

            def __class_getitem__(cls, ref_type: Any) -> Any:
                if isinstance(ref_type, TypcType) or ref_type is Void:
                    return PointerType(int_type, ref_type)
                if ref_type is ForwardRef:
                    return PointerType(int_type, None)
                return generic_class_getitem(cls, ref_type)

        return PointerSized

    def __new__(  # pylint: disable=arguments-differ
        cls,
        type_or_value: Any = None,
        value: Any = None,
    ):
        ref_type: Optional[REFX]
        if isinstance(type_or_value, TypcType) or type_or_value is Void:
            ref_type = type_or_value
        elif type_or_value is ForwardRef:
            ref_type = None
        else:
            raise TypeError
        pointer_type = PointerType(cast(TypcAtomType, cls.__typc_int_type__),
                                   ref_type)
        pointer_value = PointerValue(pointer_type, value)
        return pointer_value


class Pointer16(_Pointer[UInt16, REF], Generic[REF]):
    pass


class Pointer32(_Pointer[UInt32, REF], Generic[REF]):
    pass


class Pointer64(_Pointer[UInt64, REF], Generic[REF]):
    pass
