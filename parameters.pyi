# AUTO-GENERATED — do not edit manually.
# Regenerate with: python generate_stubs.py
# Source: platforms.toml

from __future__ import annotations
from typing import Optional, Any


class ParameterPSSE:
    param_id: str
    psseID: str
    component: str
    psseType: str
    poniter: int
    scale_factor: Optional[float] = 1.0
    def __init__(self, param_id: str, psseID: str, component: str, psseType: str, poniter: int, scale_factor: Optional[float] = 1.0) -> None: ...
    def __repr__(self) -> str: ...

class ParameterPSCAD:
    param_id: str
    pscadID: str
    component: str
    scale_factor: Optional[float] = 1.0
    def __init__(self, param_id: str, pscadID: str, component: str, scale_factor: Optional[float] = 1.0) -> None: ...
    def __repr__(self) -> str: ...

class ParameterPF:
    param_id: str
    element_type: str
    scale_factor: Optional[float] = 1.0
    default_override: Optional[float] = None
    def __init__(self, param_id: str, element_type: str, scale_factor: Optional[float] = 1.0, default_override: Optional[float] = None) -> None: ...
    def __repr__(self) -> str: ...

class ParameterTSAT:
    param_id: str
    scale_factor: Optional[float] = 1.0
    default_override: Optional[float] = None
    def __init__(self, param_id: str, scale_factor: Optional[float] = 1.0, default_override: Optional[float] = None) -> None: ...
    def __repr__(self) -> str: ...

class ParameterEMTP:
    param_id: str
    component_ref: str
    scale_factor: Optional[float] = 1.0
    default_override: Optional[float] = None
    def __init__(self, param_id: str, component_ref: str, scale_factor: Optional[float] = 1.0, default_override: Optional[float] = None) -> None: ...
    def __repr__(self) -> str: ...

class ParameterGeneral:
    param_id: str
    name: str
    description: str
    unit: str
    min: float
    max: float
    default: float
    psse: Optional[ParameterPSSE]
    pscad: Optional[ParameterPSCAD]
    pf: Optional[ParameterPF]
    tsat: Optional[ParameterTSAT]
    emtp: Optional[ParameterEMTP]
    def __init__(self, param_id: str, name: str, description: str, unit: str, min: float, max: float, default: float, psse: Optional[ParameterPSSE] = None, pscad: Optional[ParameterPSCAD] = None, pf: Optional[ParameterPF] = None, tsat: Optional[ParameterTSAT] = None, emtp: Optional[ParameterEMTP] = None) -> None: ...
    def platforms_present(self) -> list[str]: ...
    def effective_default(self, platform: str) -> float: ...
    def __repr__(self) -> str: ...

class PlatformRegistry:
    platforms: dict[str, dict]
    classes: dict[str, type]
    names: list[str]
    def __init__(self, config_path: str = ...) -> None: ...

class ParameterLoader:
    registry: PlatformRegistry
    def __init__(
        self,
        params_dir: str = ...,
        config_path: str = ...,
    ) -> None: ...
    def load(self) -> list[ParameterGeneral]: ...    
