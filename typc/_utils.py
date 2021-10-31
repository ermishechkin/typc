from __future__ import annotations

from typing import Any, Generic

generic_class_getitem = Generic.__dict__['__class_getitem__'].__func__


class _Empty:
    pass


def false_issubclass(obj: Any):
    return issubclass(obj, _Empty)


def false_isinstance(obj: Any):
    return isinstance(obj, _Empty)
