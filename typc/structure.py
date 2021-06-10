from __future__ import annotations

from struct import Struct as BuiltinStruct
from struct import calcsize
from typing import (Any, Dict, Iterable, List, Literal, Optional, Tuple, Type,
                    TypeVar, Union, cast, overload)

from ._base import BaseType, ContainerBase
from ._impl import TypcAtomType, TypcType, TypcValue
from ._meta import members_from_class

SELF = TypeVar('SELF', bound='Struct')
CLASS = TypeVar('CLASS')

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
        child_data: Optional[Tuple[TypcValue, int]] = None,
    ) -> StructValue:
        if values == 0:
            return StructValue(self, None, child_data)
        return StructValue(self, values, child_data)

    def __getattr__(self, name: str) -> TypcType:
        if name in self.__typc_members__:
            return self.__typc_members__[name][1]
        raise AttributeError

    def __getitem__(self, name: str) -> TypcType:
        if name in self.__typc_members__:
            return self.__typc_members__[name][1]
        raise KeyError


STRUCT_VALUE_ATTRS = ('__typc_type__', '__typc_child_data__',
                      '__typc_inited__', '__typc_value__')


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
        child_data: Optional[Tuple[TypcValue, int]] = None,
    ) -> None:
        self.__typc_type__ = struct_type
        self.__typc_child_data__ = child_data
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
            member_name: member_type(
                val,
                None if child_data is None else
                (self, child_data[1] + member_offset),
            )
            for (member_name, (member_offset, member_type)), val in zip(
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

    def __typc_set_part__(self, data: bytes, offset: int) -> None:
        last_byte = offset + len(data) - 1
        for name, (member_start, member_type) in (
                self.__typc_type__.__typc_members__.items()):
            if member_start > last_byte:
                break
            member_end = member_start + member_type.__typc_size__ - 1
            if member_end < offset:
                continue
            start = max(member_start, offset)
            end = min(member_end, last_byte)
            data_part = data[start - offset:end + 1 - offset]
            member_value = self.__typc_value__[name]
            if isinstance(member_value, TypcValue):
                member_value.__typc_set_part__(data_part, start - member_start)
            else:
                start_rel = start - member_start
                end_rel = end - member_start
                src_bytes = member_type.__typc_spec__.pack(member_value)
                (self.__typc_value__[name], ) = (
                    member_type.__typc_spec__.unpack(src_bytes[:start_rel] +
                                                     data_part +
                                                     src_bytes[end_rel + 1:]))

    def __typc_changed__(self, source: TypcValue, data: bytes,
                         offset: int) -> None:
        assert self.__typc_child_data__ is not None
        parent, _ = self.__typc_child_data__
        parent.__typc_changed__(self, data, offset)

    def _zero_init(self) -> None:
        child_data = self.__typc_child_data__
        self.__typc_value__ = {
            member_name: member_type(
                0,
                None if child_data is None else
                (self, child_data[1] + member_offset),
            )
            for member_name, (member_offset, member_type) in (
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
                if self.__typc_child_data__ is not None:
                    parent, self_offset = self.__typc_child_data__
                    member_offset, _ = (
                        self.__typc_type__.__typc_members__[name])
                    parent.__typc_changed__(self, bytes(current_value),
                                            self_offset + member_offset)
            else:
                member_offset, member_type = (
                    self.__typc_type__.__typc_members__[name])
                new_value = values_dict[name] = member_type(value)
                if self.__typc_child_data__ is not None:
                    parent, self_offset = self.__typc_child_data__
                    parent.__typc_changed__(
                        self, member_type.__typc_spec__.pack(new_value),
                        self_offset + member_offset)
        else:
            raise AttributeError

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
        if not self.__typc_inited__:
            self._zero_init()
        raw_value: List[Any] = []
        for value in self.__typc_value__.values():
            if isinstance(value, TypcValue):
                raw_value.append(bytes(value))
            else:
                raw_value.append(value)
        return self.__typc_type__.__typc_spec__.pack(*raw_value)


class StructMeta(type):
    def __new__(cls, name: str, bases: Tuple[type, ...],
                namespace_dict: Dict[str, Any]):
        if namespace_dict['__module__'] == __name__:
            return type.__new__(cls, name, bases, namespace_dict)
        members = members_from_class(namespace_dict)
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
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    def __typc_set__(self, value: Any) -> None:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError


class _UntypedStruct(BaseType):
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
    def __set__(self, inst: ContainerBase, value: UntypedStructValue) -> None:
        ...

    def __set__(self, inst: ContainerBase, value: Any) -> None:
        raise NotImplementedError

    def __bytes__(self) -> bytes:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    def __typc_set__(self, value: Any) -> None:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError


class UntypedStructType(_UntypedStruct):
    @overload
    def __get__(self, owner: Literal[None],
                inst: Type[ContainerBase]) -> UntypedStructType:
        ...

    @overload
    def __get__(self, owner: ContainerBase,
                inst: Type[ContainerBase]) -> UntypedStructValue:
        ...

    @overload
    def __get__(self, owner: Optional[CLASS],
                inst: Type[CLASS]) -> UntypedStructType:
        ...

    def __get__(
            self, owner: Optional[Any],
            inst: Type[Any]) -> Union[UntypedStructType, UntypedStructValue]:
        raise NotImplementedError

    def __getitem__(self, field: str) -> Type[BaseType]:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    @overload
    def __call__(self, values: Literal[None] = None) -> UntypedStructValue:
        ...

    @overload
    def __call__(self, values: Literal[0]) -> UntypedStructValue:
        ...

    @overload
    def __call__(self, values: UntypedStructValue) -> UntypedStructValue:
        ...

    @overload
    def __call__(self, values: bytes) -> UntypedStructValue:
        ...

    @overload
    def __call__(self, values: Tuple[Any, ...]) -> UntypedStructValue:
        ...

    def __call__(self, values: Any = None) -> UntypedStructValue:
        # pylint: disable=super-init-not-called
        raise NotImplementedError


class UntypedStructValue(_UntypedStruct):
    @overload
    def __get__(self, owner: Literal[None],
                inst: Type[ContainerBase]) -> UntypedStructType:
        ...

    @overload
    def __get__(self, owner: ContainerBase,
                inst: Type[ContainerBase]) -> UntypedStructValue:
        ...

    @overload
    def __get__(self, owner: Optional[CLASS],
                inst: Type[CLASS]) -> UntypedStructValue:
        ...

    def __get__(
            self, owner: Optional[Any],
            inst: Type[Any]) -> Union[UntypedStructType, UntypedStructValue]:
        raise NotImplementedError

    def __getitem__(self, field: str) -> Any:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError

    def __setitem__(self, field: str, value: Any) -> None:
        ...  # mark as non-abstract for pylint
        raise NotImplementedError


def create_struct(
    name: str,
    fields: Dict[str, Union[BaseType, Type[BaseType]]],
) -> UntypedStructType:
    if not fields:
        raise ValueError('No members declared')
    fields_: Dict[str, Any] = fields
    members: Dict[str, TypcType] = {}
    for member_name, member_value in fields_.items():
        if isinstance(member_value, TypcType):
            members[member_name] = member_value
        elif isinstance(member_value, TypcValue):
            members[member_name] = member_value.__typc_type__
        else:
            raise ValueError('Only type members are allowed')
    return cast(UntypedStructType, StructType(name, members))
