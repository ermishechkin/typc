from __future__ import annotations

import inspect
from types import FrameType
from typing import Any, Dict, Mapping, Optional, Tuple, Union

from ._impl import TypcType, TypcValue
from ._modifier import Modified
from .modifier import Padding, Shift

MEMBER = Union[TypcType, Padding[Any], Modified]
MAP = Mapping[str, MEMBER]


def _eval_member(annotation: Any, globals_dict: Dict[str, Any],
                 locals_dict: Dict[str, Any]) -> MEMBER:
    if isinstance(annotation, str):
        # pylint: disable=eval-used
        field_type = eval(annotation, globals_dict, locals_dict)
    else:
        field_type = annotation
    if isinstance(field_type, TypcType):
        return field_type
    if isinstance(field_type, TypcValue):
        return field_type.__typc_type__
    if isinstance(field_type, Padding):
        return field_type  # type: ignore
    modified = parse_annotated(field_type)
    if modified is not None:
        return modified
    raise ValueError(f'{annotation} is not a valid type')


def parse_annotated(
        anotation_value: Any) -> Optional[Union[TypcType, Modified]]:
    origin = getattr(anotation_value, '__origin__', None)
    metadata: Optional[Tuple[Any, ...]]
    metadata = getattr(anotation_value, '__metadata__', None)
    if not isinstance(origin, TypcType):
        return None
    assert isinstance(metadata, tuple)
    padding = 0
    shift = 0
    for meta in metadata:
        if isinstance(meta, Padding):
            padding = int(meta.__typc_padding__)
        elif isinstance(meta, Shift):
            shift = int(meta.__typc_shift__)
    if shift != 0 or padding != 0:
        return Modified(origin, shift=shift, padding=padding)
    return origin


def members_from_annotations(cls_dict: Dict[str, Any],
                             caller_frame: FrameType) -> MAP:
    cls_annotations: Dict[str, Any] = cls_dict.get('__annotations__', {})
    fields = {
        name: _eval_member(value, caller_frame.f_globals,
                           caller_frame.f_locals)
        for name, value in cls_annotations.items()
    }
    return fields


def members_from_classvars(cls_dict: Dict[str, Any]) -> MAP:
    result: Dict[str, MEMBER] = {}
    for name, value in cls_dict.items():
        if name in CLS_MEMBERS:
            continue
        if isinstance(value, (TypcType, Padding, Modified)):
            result[name] = value
        elif isinstance(value, TypcValue):
            result[name] = value.__typc_type__
        else:
            raise ValueError('Only type members are allowed')
    return result


def validate_and_union_members(members1: MAP, members2: MAP) -> MAP:
    if members1 and not members2:
        return members1
    if members2 and not members1:
        return members2
    if not members1 and not members2:
        raise ValueError('No members declared')
    raise ValueError('Both members and annotations not supported')


def members_from_class(cls_dict: Dict[str, Any]) -> MAP:
    members1: MAP
    if '__annotations__' in cls_dict:
        this_frame = inspect.currentframe()
        assert this_frame is not None
        metaclass_frmae = this_frame.f_back
        assert metaclass_frmae is not None
        caller_frame = metaclass_frmae.f_back
        assert caller_frame is not None
        members1 = members_from_annotations(cls_dict, caller_frame)
    else:
        members1 = {}
    members2 = members_from_classvars(cls_dict)
    members = validate_and_union_members(members1, members2)
    return members


CLS_MEMBERS = ('__annotations__', '__module__', '__qualname__', '__doc__')
