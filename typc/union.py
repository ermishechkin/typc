from __future__ import annotations

from struct import Struct as BuiltinStruct
from typing import Any, Dict, Literal, Optional, Tuple, Type, TypeVar
from typing import Union as TypingUnion
from typing import cast, overload

from ._base import BaseType, ContainerBase
from ._impl import TypcType, TypcValue
from ._meta import MAP, MEMBER, members_from_class
from ._modifier import Modified
from .modifier import Padding

SELF = TypeVar('SELF', bound='Union')
CLASS = TypeVar('CLASS')

_object_setattr = object.__setattr__


class UnionType(TypcType):
    __slots__ = ('__typc_name__', '__typc_members__')

    __typc_members__: Dict[str, Tuple[int, TypcType]]

    def __init__(self, name: str, members: MAP) -> None:
        self.__typc_name__ = name
        members_dict: Dict[str, Tuple[int, TypcType]]
        members_dict = self.__typc_members__ = {}
        max_size = 0
        for member_name, member_type in members.items():
            if isinstance(member_type, TypcType):
                members_dict[member_name] = (0, member_type)
                member_size = member_type.__typc_size__
            elif isinstance(member_type, Padding):
                member_size = member_type.__typc_padding__
            else:  # Modified
                shift = member_type.__typc_shift__
                real_type = member_type.__typc_real_type__
                members_dict[member_name] = (shift, real_type)
                member_size = (shift + real_type.__typc_size__ +
                               member_type.__typc_padding__)
            if member_size > max_size:
                max_size = member_size
        self.__typc_size__ = max_size
        self.__typc_spec__ = BuiltinStruct(f'<{max_size}s')

    def __call__(
        self,
        values: TypingUnion[Literal[None], Literal[0], bytes,
                            UnionValue] = None,
        child_data: Optional[Tuple[TypcValue, int]] = None,
    ) -> UnionValue:
        if values == 0:
            return UnionValue(self, None, child_data)
        return UnionValue(self, values, child_data)

    def __getattr__(self, name: str) -> TypcType:
        if name in self.__typc_members__:
            return self.__typc_members__[name][1]
        raise AttributeError

    def __getitem__(self, name: str) -> TypcType:
        if name in self.__typc_members__:
            return self.__typc_members__[name][1]
        raise KeyError


UNION_VALUE_ATTRS = ('__typc_type__', '__typc_child_data__', '__typc_value__',
                     '__typc_raw__')


class UnionValue(TypcValue):
    __slots__ = ('__typc_value__', '__typc_raw__')

    __typc_type__: UnionType
    __typc_value__: Dict[str, Optional[TypingUnion[TypcValue, Any]]]
    __typc_raw__: bytes

    def __init__(
        self,
        union_type: UnionType,
        values: Optional[TypingUnion[bytes, UnionValue, Literal[None],
                                     Literal[0]]],
        child_data: Optional[Tuple[TypcValue, int]] = None,
    ) -> None:
        self.__typc_type__ = union_type
        self.__typc_child_data__ = child_data
        if values in (None, 0):
            value_raw = bytes(union_type.__typc_size__)
        elif isinstance(values, bytes):
            value_raw = values
        elif isinstance(values, UnionValue):
            value_raw = bytes(values)
        else:
            raise TypeError
        self.__typc_raw__ = value_raw
        self.__typc_value__ = {
            member_name: None
            for member_name in union_type.__typc_members__.keys()
        }

    def __typc_set__(self, value: Any) -> None:
        self_type = self.__typc_type__
        new_value: bytes
        if value in (None, 0):
            new_value = bytes(self_type.__typc_size__)
        elif isinstance(value, bytes):
            new_value = value
        elif isinstance(value, UnionValue):
            new_value = bytes(value)
        else:
            raise TypeError
        self.__typc_raw__ = new_value
        values_dict = self.__typc_value__
        for ((member_name, (member_offset, member_type)),
             prev_val) in zip(self_type.__typc_members__.items(),
                              tuple(values_dict.values())):
            if prev_val is None:
                continue
            member_raw = new_value[member_offset:member_offset +
                                   member_type.__typc_size__]
            if isinstance(prev_val, TypcValue):
                prev_val.__typc_set__(member_raw)
            else:
                values_dict[member_name] = member_type(member_raw)

    def __typc_set_part__(self, data: bytes, offset: int) -> None:
        self._set_part_impl(data, offset, None)

    def __typc_changed__(self, source: TypcValue, data: bytes,
                         offset: int) -> None:
        self._set_part_impl(data, offset, source)

    def _set_part_impl(self, data: bytes, offset: int,
                       exclude: Optional[TypcValue]) -> None:
        prev_raw = self.__typc_raw__
        self.__typc_raw__ = new_raw = (prev_raw[:offset] + data +
                                       prev_raw[offset + len(data):])
        for name, (member_offset, member_type) in (
                self.__typc_type__.__typc_members__.items()):
            member_size = member_type.__typc_size__
            offset_diff = member_offset - offset
            if (offset_diff >= len(data)) or (member_size + offset_diff <= 0):
                continue
            member_value = self.__typc_value__[name]
            if member_value is None:
                continue
            if isinstance(member_value, TypcValue):
                if member_value is not exclude:
                    if member_offset <= offset:
                        member_value.__typc_set_part__(
                            data[:member_size + offset_diff], -offset_diff)
                    else:
                        member_value.__typc_set_part__(
                            data[offset_diff:offset_diff + member_size], 0)
            else:
                (self.__typc_value__[name], ) = (
                    member_type.__typc_spec__.unpack(
                        new_raw[member_offset:member_offset + member_size]))
        if exclude is not None and self.__typc_child_data__ is not None:
            parent, self_offset = self.__typc_child_data__
            parent.__typc_changed__(self, data, self_offset + offset)

    def __getattr__(self, name: str) -> Any:
        if name not in self.__typc_value__:
            raise AttributeError
        value = self.__typc_value__[name]
        if value is None:
            member_offset, member_type = (
                self.__typc_type__.__typc_members__[name])
            value = member_type(
                self.__typc_raw__[member_offset:member_offset +
                                  member_type.__typc_size__],
                (self, member_offset))
            self.__typc_value__[name] = value
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        if name in UNION_VALUE_ATTRS:
            _object_setattr(self, name, value)
            return
        values_dict = self.__typc_value__
        if name not in values_dict:
            raise AttributeError
        member_value = values_dict[name]
        member_offset, member_type = self.__typc_type__.__typc_members__[name]
        if member_value is None:
            new_value = member_type(value, (self, member_offset))
            values_dict[name] = new_value
        elif isinstance(member_value, TypcValue):
            member_value.__typc_set__(value)
            new_value = member_value
        else:
            new_value = member_type(value)
            values_dict[name] = new_value
        if isinstance(new_value, TypcValue):
            self._set_part_impl(bytes(new_value), member_offset, new_value)
        else:
            self._set_part_impl(member_type.__typc_spec__.pack(new_value),
                                member_offset, None)

    def __getitem__(self, name: str) -> Any:
        try:
            return getattr(self, name)
        except AttributeError:
            raise KeyError from None

    def __setitem__(self, name: str, value: Any) -> None:
        try:
            return setattr(self, name, value)
        except AttributeError:
            raise KeyError from None

    def __bytes__(self) -> bytes:
        return self.__typc_raw__


class UnionMeta(type):
    def __new__(cls, name: str, bases: Tuple[type, ...],
                namespace_dict: Dict[str, Any]):
        if namespace_dict['__module__'] == __name__:
            return type.__new__(cls, name, bases, namespace_dict)
        members = members_from_class(namespace_dict)
        return UnionType(name, members)


class Union(ContainerBase, metaclass=UnionMeta):
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
    def __set__(self: SELF, inst: ContainerBase, value: SELF) -> None:
        ...

    def __set__(self: SELF, inst: ContainerBase,
                value: TypingUnion[Literal[0], bytes, SELF]) -> None:
        raise NotImplementedError

    def __bytes__(self) -> bytes:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    def __typc_set__(self, value: Any) -> None:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError


class _UntypedUnion(BaseType):
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
    def __set__(self, inst: ContainerBase, value: UntypedUnionValue) -> None:
        ...

    def __set__(self, inst: ContainerBase, value: Any) -> None:
        raise NotImplementedError

    def __bytes__(self) -> bytes:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    def __typc_set__(self, value: Any) -> None:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError


class UntypedUnionType(_UntypedUnion):
    @overload
    def __get__(self, owner: Literal[None],
                inst: Type[ContainerBase]) -> UntypedUnionType:
        ...

    @overload
    def __get__(self, owner: ContainerBase,
                inst: Type[ContainerBase]) -> UntypedUnionValue:
        ...

    @overload
    def __get__(self, owner: Optional[CLASS],
                inst: Type[CLASS]) -> UntypedUnionType:
        ...

    def __get__(
            self, owner: Optional[Any], inst: Type[Any]
    ) -> TypingUnion[UntypedUnionType, UntypedUnionValue]:
        raise NotImplementedError

    def __getitem__(self, field: str) -> Type[BaseType]:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    @overload
    def __call__(self, values: Literal[None] = None) -> UntypedUnionValue:
        ...

    @overload
    def __call__(self, values: Literal[0]) -> UntypedUnionValue:
        ...

    @overload
    def __call__(self, values: UntypedUnionValue) -> UntypedUnionValue:
        ...

    @overload
    def __call__(self, values: bytes) -> UntypedUnionValue:
        ...

    @overload
    def __call__(self, values: Tuple[Any, ...]) -> UntypedUnionValue:
        ...

    def __call__(self, values: Any = None) -> UntypedUnionValue:
        # pylint: disable=super-init-not-called
        raise NotImplementedError


class UntypedUnionValue(_UntypedUnion):
    @overload
    def __get__(self, owner: Literal[None],
                inst: Type[ContainerBase]) -> UntypedUnionType:
        ...

    @overload
    def __get__(self, owner: ContainerBase,
                inst: Type[ContainerBase]) -> UntypedUnionValue:
        ...

    @overload
    def __get__(self, owner: Optional[CLASS],
                inst: Type[CLASS]) -> UntypedUnionValue:
        ...

    def __get__(
            self, owner: Optional[Any], inst: Type[Any]
    ) -> TypingUnion[UntypedUnionType, UntypedUnionValue]:
        raise NotImplementedError

    def __getitem__(self, field: str) -> Any:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    def __setitem__(self, field: str, value: Any) -> None:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError


def create_union(
    name: str,
    fields: Dict[str, TypingUnion[BaseType, Type[BaseType], Type[Padding[Any]],
                                  Padding[Any]]],
) -> UntypedUnionType:
    if not fields:
        raise ValueError('No members declared')
    fields_: Dict[str, Any] = fields
    members: Dict[str, MEMBER] = {}
    for member_name, member_value in fields_.items():
        if isinstance(member_value, (TypcType, Padding, Modified)):
            members[member_name] = member_value
        elif isinstance(member_value, TypcValue):
            members[member_name] = member_value.__typc_type__
        else:
            raise ValueError('Only type members are allowed')
    return cast(UntypedUnionType, UnionType(name, members))
