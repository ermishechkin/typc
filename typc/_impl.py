from __future__ import annotations

from math import ceil, floor, trunc
from operator import (add, and_, floordiv, ge, gt, invert, le, lshift, lt, mod,
                      mul, neg, or_, pos, rshift, sub, truediv, xor)
from struct import Struct as BuiltinStruct
from typing import Any, Callable, Dict, Literal, Optional, Tuple, Union

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


class TypcAtomBaseMeta(type):
    __typc_native__: type

    def __new__(
        cls,
        name: str,
        bases: Tuple[type, ...],
        namespace_dict: Dict[str, Any],
        *,
        native_type: Optional[type] = None,
    ):
        if namespace_dict['__module__'] == __name__:
            return type.__new__(cls, name, bases, namespace_dict)
        if native_type is not None:
            return type.__new__(cls, name, bases, {
                '__typc_native__': native_type,
                **namespace_dict
            })
        return TypcAtomType(namespace_dict['__typc_name__'],
                            namespace_dict['__typc_spec__'],
                            namespace_dict['__typc_size__'],
                            namespace_dict['__typc_native__'])

    def __subclasscheck__(cls, subclass: Any) -> bool:
        if isinstance(subclass, TypcAtomType):
            return subclass.__typc_native__ == cls.__typc_native__
        if subclass is cls:
            return True
        return false_issubclass(subclass)

    def __instancecheck__(cls, instance: Any) -> bool:
        if isinstance(instance, TypcAtomValue):
            return (
                instance.__typc_type__.__typc_native__ == cls.__typc_native__)
        return false_isinstance(instance)


class TypcAtomBase(type, metaclass=TypcAtomBaseMeta):
    pass


class TypcAtomType(TypcType):
    __slots__ = ('__typc_native__', '__typc_value_type__')
    __typc_native__: type
    __typc_name__: str

    def __init__(self, name: str, spec: str, size: int,
                 native_type: type) -> None:
        self.__typc_spec__ = BuiltinStruct(spec)
        self.__typc_size__ = size
        self.__typc_name__ = name
        self.__typc_native__ = native_type
        self.__typc_value_type__ = TypcAtomValue
        if native_type is int:
            self.__typc_value_type__ = TypcIntegerValue
        elif native_type is float:
            self.__typc_value_type__ = TypcFloatValue

    def __call__(
        self,
        values: Any = None,
        child_data: Optional[Tuple[TypcValue, int]] = None,
    ) -> TypcAtomValue:
        return self.__typc_value_type__(self, values, child_data)

    def __typc_get_name__(self) -> str:
        return self.__typc_name__

    def __typc_clone__(self) -> TypcAtomType:
        new_type: TypcAtomType = TypcAtomType.__new__(TypcAtomType)
        new_type.__typc_spec__ = self.__typc_spec__
        new_type.__typc_size__ = self.__typc_size__
        new_type.__typc_name__ = self.__typc_name__
        new_type.__typc_native__ = self.__typc_native__
        new_type.__typc_value_type__ = self.__typc_value_type__
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
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    def __eq__(self, obj: Any) -> bool:
        return self.__typc_value__ == obj


def create_unary_method(operator: Callable[[Any], Any]):
    def method(self: TypcAtomValue) -> Any:
        return operator(self.__typc_value__)

    return method


def create_left_method(operator: Callable[[Any, Any], Any]):
    def method(self: TypcAtomValue, obj: Any) -> Any:
        if isinstance(obj, TypcAtomValue):
            return operator(self.__typc_value__, obj.__typc_value__)
        return operator(self.__typc_value__, obj)

    return method


def create_right_method(operator: Callable[[Any, Any], Any]):
    def method(self: TypcAtomValue, obj: Any) -> Any:
        # if obj is TypcAtomValue then it is already handled by left method
        return operator(obj, self.__typc_value__)

    return method


def create_inplace_method(operator: Callable[[Any, Any], Any]):
    def method(self: TypcAtomValue, obj: Any) -> Any:
        native_type = self.__typc_type__.__typc_native__
        if isinstance(obj, TypcAtomValue):
            self.__typc_value__ = native_type(
                operator(self.__typc_value__, obj.__typc_value__))
        else:
            self.__typc_value__ = native_type(
                operator(self.__typc_value__, obj))
        return self

    return method


class TypcIntegerValue(TypcAtomValue):
    def __index__(self) -> int:
        return self.__typc_value__

    __abs__ = create_unary_method(abs)
    __bool__ = create_unary_method(bool)
    __ceil__ = create_unary_method(ceil)
    __float__ = create_unary_method(float)
    __floor__ = create_unary_method(floor)
    __int__ = create_unary_method(int)
    __invert__ = create_unary_method(invert)
    __neg__ = create_unary_method(neg)
    __pos__ = create_unary_method(pos)
    __round__ = create_unary_method(round)
    __trunc__ = create_unary_method(trunc)

    __add__ = create_left_method(add)
    __and__ = create_left_method(and_)
    __divmod__ = create_left_method(divmod)
    __floordiv__ = create_left_method(floordiv)
    __lshift__ = create_left_method(lshift)
    __mod__ = create_left_method(mod)
    __mul__ = create_left_method(mul)
    __or__ = create_left_method(or_)
    __pow__ = create_left_method(pow)
    __rshift__ = create_left_method(rshift)
    __sub__ = create_left_method(sub)
    __truediv__ = create_left_method(truediv)
    __xor__ = create_left_method(xor)

    __radd__ = create_right_method(add)
    __rand__ = create_right_method(and_)
    __rdivmod__ = create_right_method(divmod)
    __rfloordiv__ = create_right_method(floordiv)
    __rlshift__ = create_right_method(lshift)
    __rmod__ = create_right_method(mod)
    __rmul__ = create_right_method(mul)
    __ror__ = create_right_method(or_)
    __rpow__ = create_right_method(pow)
    __rrshift__ = create_right_method(rshift)
    __rsub__ = create_right_method(sub)
    __rtruediv__ = create_right_method(truediv)
    __rxor__ = create_right_method(xor)

    __ge__ = create_left_method(ge)
    __gt__ = create_left_method(gt)
    __le__ = create_left_method(le)
    __lt__ = create_left_method(lt)

    __iadd__ = create_inplace_method(add)
    __iand__ = create_inplace_method(and_)
    __ifloordiv__ = create_inplace_method(floordiv)
    __ilshift__ = create_inplace_method(lshift)
    __imod__ = create_inplace_method(mod)
    __imul__ = create_inplace_method(mul)
    __ior__ = create_inplace_method(or_)
    __ipow__ = create_inplace_method(pow)
    __irshift__ = create_inplace_method(rshift)
    __isub__ = create_inplace_method(sub)
    __itruediv__ = create_inplace_method(truediv)
    __ixor__ = create_inplace_method(xor)


class TypcFloatValue(TypcAtomValue):
    __abs__ = create_unary_method(abs)
    __bool__ = create_unary_method(bool)
    __float__ = create_unary_method(float)
    __int__ = create_unary_method(int)
    __neg__ = create_unary_method(neg)
    __pos__ = create_unary_method(pos)
    __round__ = create_unary_method(round)
    __trunc__ = create_unary_method(trunc)

    __add__ = create_left_method(add)
    __divmod__ = create_left_method(divmod)
    __floordiv__ = create_left_method(floordiv)
    __mod__ = create_left_method(mod)
    __mul__ = create_left_method(mul)
    __sub__ = create_left_method(sub)
    __truediv__ = create_left_method(truediv)

    __radd__ = create_right_method(add)
    __rdivmod__ = create_right_method(divmod)
    __rfloordiv__ = create_right_method(floordiv)
    __rmod__ = create_right_method(mod)
    __rmul__ = create_right_method(mul)
    __rsub__ = create_right_method(sub)
    __rtruediv__ = create_right_method(truediv)

    __ge__ = create_left_method(ge)
    __gt__ = create_left_method(gt)
    __le__ = create_left_method(le)
    __lt__ = create_left_method(lt)

    __iadd__ = create_inplace_method(add)
    __ifloordiv__ = create_inplace_method(floordiv)
    __imod__ = create_inplace_method(mod)
    __imul__ = create_inplace_method(mul)
    __isub__ = create_inplace_method(sub)
    __itruediv__ = create_inplace_method(truediv)
