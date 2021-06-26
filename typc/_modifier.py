from __future__ import annotations

from ._impl import TypcType


class Modified:
    __slots__ = ('__typc_real_type__', '__typc_shift__', '__typc_padding__')

    def __init__(
        self,
        real_type: TypcType,
        *,
        shift: int = 0,
        padding: int = 0,
    ) -> None:
        self.__typc_real_type__ = real_type
        self.__typc_shift__ = shift
        self.__typc_padding__ = padding
