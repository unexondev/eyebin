from __future__ import annotations

from typing import Callable
from typing import TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from .resolver import PVID

from eyebin.core.sensor import Sensor
from eyebin.stream.profile import StreamProfile

from .impl.realsense import resolve as rs_resolve


@dataclass(frozen=True)
class PVID:
    product_id : int
    vendor_id : int


DESCS : dict[PVID, Callable[[StreamProfile], Sensor]] = {

    PVID(product_id=0x0AD3, vendor_id=0x8086): rs_resolve
    
}