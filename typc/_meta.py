from __future__ import annotations

import inspect
from types import FrameType
from typing import Any, Dict

from ._impl import TypcType, TypcValue

MAP = Dict[str, TypcType]


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


CLS_MEMBERS = ('__annotations__', '__module__', '__qualname__')
