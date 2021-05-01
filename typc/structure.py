from __future__ import annotations

import inspect
from struct import Struct as BuiltinStruct
from struct import calcsize
from types import FrameType
from typing import (Any, Dict, Iterable, List, Literal, Optional, Tuple,
                    TypeVar, Union, overload)

from ._base import ContainerBase
from ._impl import TypcAtomType, TypcType, TypcValue

MAP = Dict[str, TypcType]
SELF = TypeVar('SELF', bound='Struct')

CLS_MEMBERS = ('__annotations__', '__module__', '__qualname__')
_object_setattr = object.__setattr__


def spec_from_fields(fields: Iterable[TypcType]) -> Tuple[str, int]:
    spec = ''.join(((x.__typc_spec__.format
                     if isinstance(x, TypcAtomType) else f'{x.__typc_size__}s')
                    for x in fields))
    return spec, calcsize('<' + spec)


class StructType(TypcType):
    __slots__ = ('__typc_name__', '__typc_members__')

    __typc_members__: Dict[str, Tuple[int, TypcType]]

    def __init__(self, name: str, members: Dict[str, TypcType]) -> None:
        self.__typc_name__ = name
        offset = 0
        members_dict = self.__typc_members__ = {}
        for member_name, member_type in members.items():
            members_dict[member_name] = (offset, member_type)
            offset += member_type.__typc_size__
        spec, size = spec_from_fields(members.values())  # type: ignore
        self.__typc_spec__ = BuiltinStruct('<' + spec)
        self.__typc_size__ = size

    def __call__(
        self,
        values: Union[Literal[None], Literal[0], bytes, Tuple[Any, ...],
                      StructValue] = None,
    ) -> StructValue:
        if values == 0:
            return StructValue(self, None)
        return StructValue(self, values)

    def __getattr__(self, name: str) -> TypcType:
        if name in self.__typc_members__:
            return self.__typc_members__[name][1]
        raise AttributeError


STRUCT_VALUE_ATTRS = ('__typc_type__', '__typc_inited__', '__typc_value__')


class StructValue(TypcValue):
    __slots__ = ('__typc_inited__', '__typc_value__')

    __typc_type__: StructType
    __typc_inited__: bool
    __typc_value__: Dict[str, Union[TypcValue, Any]]

    def __init__(
        self,
        struct_type: StructType,
        values: Optional[Union[Tuple[Any, ...], bytes, StructValue,
                               Literal[None], Literal[0]]],
    ) -> None:
        self.__typc_type__ = struct_type
        if values in (None, 0):
            self.__typc_inited__ = False
            return
        if isinstance(values, bytes):
            values_tuple = struct_type.__typc_spec__.unpack(values)
        elif isinstance(values, StructValue):
            values_tuple = struct_type.__typc_spec__.unpack(bytes(values))
        elif isinstance(values, tuple):
            values_tuple = values
        else:
            raise TypeError
        self.__typc_value__ = {
            member_name: member_type(val)
            for (member_name, (_, member_type)), val in zip(
                struct_type.__typc_members__.items(), values_tuple)
        }
        self.__typc_inited__ = True

    def __typc_set__(self, value: Any) -> None:
        if not self.__typc_inited__:
            self.__init__(self.__typc_type__, value)  # type: ignore
            return
        self_type = self.__typc_type__
        new_values: Tuple[Any, ...]
        if value in (None, 0):
            new_values = (0, ) * len(self_type.__typc_members__)
        elif isinstance(value, bytes):
            new_values = self_type.__typc_spec__.unpack(value)
        elif isinstance(value, StructValue):
            new_values = self_type.__typc_spec__.unpack(bytes(value))
        elif isinstance(value, tuple):
            new_values = value
        else:
            raise TypeError
        values_dict = self.__typc_value__
        for ((member_name, (_, member_type)), prev_val,
             new_val) in zip(self_type.__typc_members__.items(),
                             list(values_dict.values()), new_values):
            if isinstance(prev_val, TypcValue):
                prev_val.__typc_set__(new_val)
            else:
                values_dict[member_name] = member_type(new_val)

    def _zero_init(self) -> None:
        self.__typc_value__ = {
            member_name: member_type(0)
            for member_name, (_, member_type) in (
                self.__typc_type__.__typc_members__.items())
        }
        self.__typc_inited__ = True

    def __getattr__(self, name: str) -> Any:
        if not self.__typc_inited__:
            self._zero_init()
        if name in self.__typc_value__:
            return self.__typc_value__[name]
        raise AttributeError

    def __setattr__(self, name: str, value: Any) -> None:
        if name in STRUCT_VALUE_ATTRS:
            _object_setattr(self, name, value)
            return
        if not self.__typc_inited__:
            self._zero_init()
        values_dict = self.__typc_value__
        if name in values_dict:
            current_value = values_dict[name]
            if isinstance(current_value, TypcValue):
                current_value.__typc_set__(value)
            else:
                _, member_type = self.__typc_type__.__typc_members__[name]
                values_dict[name] = member_type(value)
        else:
            raise AttributeError

    def __bytes__(self) -> bytes:
        if not self.__typc_inited__:
            self._zero_init()
        raw_value: List[Any] = []
        for value in self.__typc_value__.values():
            if isinstance(value, TypcValue):
                raw_value.append(bytes(value))
            else:
                raw_value.append(value)
        return self.__typc_type__.__typc_spec__.pack(*raw_value)


def _eval_member(annotation: Any, globals_dict: Dict[str, Any],
                 locals_dict: Dict[str, Any]) -> Any:
    if isinstance(annotation, str):
        # pylint: disable=eval-used
        field_type = eval(annotation, globals_dict, locals_dict)
    else:
        field_type = annotation
    if isinstance(field_type, TypcType):
        return field_type
    if isinstance(field_type, TypcValue):
        return field_type.__typc_type__
    raise ValueError(f'{annotation} is not a valid type')


def _members_from_annotations(cls_dict: Dict[str, Any],
                              caller_frame: FrameType) -> MAP:
    cls_annotations: Dict[str, Any] = cls_dict.get('__annotations__', {})
    fields = {
        name: _eval_member(value, caller_frame.f_globals,
                           caller_frame.f_locals)
        for name, value in cls_annotations.items()
    }
    return fields


def _members_from_classvars(cls_dict: Dict[str, Any]) -> MAP:
    result: MAP = {}
    for name, value in cls_dict.items():
        if name in CLS_MEMBERS:
            continue
        if isinstance(value, TypcType):
            result[name] = value
        elif isinstance(value, TypcValue):
            result[name] = value.__typc_type__
        else:
            raise ValueError('Only type members are allowed')
    return result


def _validate_and_union_members(members1: MAP, members2: MAP) -> MAP:
    if members1 and not members2:
        return members1
    if members2 and not members1:
        return members2
    if not members1 and not members2:
        raise ValueError('No members declared')
    raise ValueError('Both members and annotations not supported')


def _members_from_class(cls_dict: Dict[str, Any]) -> MAP:
    members1: MAP
    if '__annotations__' in cls_dict:
        this_frame = inspect.currentframe()
        assert this_frame is not None
        metaclass_frmae = this_frame.f_back
        assert metaclass_frmae is not None
        caller_frame = metaclass_frmae.f_back
        assert caller_frame is not None
        members1 = _members_from_annotations(cls_dict, caller_frame)
    else:
        members1 = {}
    members2 = _members_from_classvars(cls_dict)
    members = _validate_and_union_members(members1, members2)
    return members


class StructMeta(type):
    def __new__(cls, name: str, bases: Tuple[type, ...],
                namespace_dict: Dict[str, Any]):
        if namespace_dict['__module__'] == __name__:
            return type.__new__(cls, name, bases, namespace_dict)
        members = _members_from_class(namespace_dict)
        return StructType(name, members)


class Struct(ContainerBase, metaclass=StructMeta):
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
    def __init__(self, values: Tuple[Any, ...]) -> None:
        ...

    def __init__(self, values: Any = None) -> None:
        # pylint: disable=super-init-not-called
        raise NotImplementedError

    @overload
    def __set__(self, inst: ContainerBase, value: Literal[0]) -> None:
        ...

    @overload
    def __set__(self, inst: ContainerBase, value: bytes) -> None:
        ...

    @overload
    def __set__(self, inst: ContainerBase, value: Tuple[Any, ...]) -> None:
        ...

    @overload
    def __set__(self: SELF, inst: ContainerBase, value: SELF) -> None:
        ...

    def __set__(self, inst: ContainerBase, value: Any) -> None:
        raise NotImplementedError

    def __bytes__(self) -> bytes:
        raise NotImplementedError

    def __typc_set__(self, value: Any) -> None:
        raise NotImplementedError
