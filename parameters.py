# parameters.py
# DO NOT import from parameters.pyi — that file is for the IDE only.
from __future__ import annotations

from dataclasses import dataclass, field, make_dataclass
from typing import Any, Optional
import os

import pandas as pd

try:
    import tomllib          # Python 3.11+
except ImportError:
    import tomli as tomllib  # pip install tomli


# ─────────────────────────────────────────────
# Mapa de tipos Python
# ─────────────────────────────────────────────

TYPE_MAP: dict[str, type] = {
    "str":   str,
    "float": float,
    "int":   int,
    "bool":  bool,
}


# ─────────────────────────────────────────────
# PlatformRegistry
# ─────────────────────────────────────────────

class PlatformRegistry:
    """
    Lee platforms.toml y genera dinámicamente las clases ParameterX.
    Es la única parte del sistema que conoce platforms.toml.
    """

    def __init__(self, config_path: str = "platforms.toml") -> None:
        with open(config_path, "rb") as f:
            raw = tomllib.load(f)

        self.platforms: dict[str, dict] = {}
        self.classes:   dict[str, type] = {}

        for p in raw["platforms"]:
            name = p["name"]
            self.platforms[name] = self._parse_config(p)
            self.classes[name]   = self._make_class(name, p["fields"])

    def _parse_config(self, p: dict) -> dict:
        required: list[str] = []
        optional: dict[str, Any] = {}

        for f in p["fields"]:
            if f["required"]:
                required.append(f["name"])
            else:
                raw_default = f.get("default")
                optional[f["name"]] = None if raw_default == "null" else raw_default

        return {"required": required, "optional": optional, "fields": p["fields"]}

    def _make_class(self, name: str, fields: list[dict]) -> type:
        """Genera dinámicamente una dataclass para la plataforma."""
        class_fields: list = [("param_id", str)]

        for f in fields:
            python_type = TYPE_MAP[f["type"]]
            if f["required"]:
                class_fields.append((f["name"], python_type))
            else:
                raw_default = f.get("default")
                default_val = None if raw_default == "null" else raw_default
                class_fields.append((
                    f["name"],
                    Optional[python_type],
                    field(default=default_val),
                ))

        return make_dataclass(f"Parameter{name.upper()}", class_fields)

    @property
    def names(self) -> list[str]:
        return list(self.platforms.keys())


# ─────────────────────────────────────────────
# ParameterGeneral
# ─────────────────────────────────────────────

@dataclass
class ParameterGeneral:
    param_id:    str
    name:        str
    description: str
    unit:        str
    min:         float
    max:         float
    default:     float

    def _attach_platforms(self, registry: PlatformRegistry) -> None:
        """Añade un atributo por plataforma, inicializado a None."""
        for name in registry.names:
            if not hasattr(self, name):
                setattr(self, name, None)

    def platforms_present(self) -> list[str]:
        """Devuelve los nombres de las plataformas donde este parámetro está definido."""
        reserved = {"param_id", "name", "description", "unit", "min", "max", "default"}
        return [
            k for k, v in self.__dict__.items()
            if k not in reserved and v is not None
        ]

    def effective_default(self, platform: str) -> float:
        """
        Devuelve el default efectivo para una plataforma:
        usa default_override si está definido, si no el default general.
        """
        p = getattr(self, platform, None)
        if p is None:
            raise ValueError(
                f"El parámetro '{self.param_id}' no está presente en la plataforma '{platform}'"
            )
        override = getattr(p, "default_override", None)
        return override if override is not None else self.default


# ─────────────────────────────────────────────
# ParameterLoader
# ─────────────────────────────────────────────

class ParameterLoader:
    """
    Carga general.csv y los CSVs de cada plataforma.
    Construye y devuelve una lista de ParameterGeneral con sus plataformas enlazadas.
    """

    def __init__(
        self,
        params_dir:  str = "params",
        config_path: str = "platforms.toml",
    ) -> None:
        self.params_dir = params_dir
        self.registry   = PlatformRegistry(config_path)

    def _csv_path(self, name: str) -> str:
        return os.path.join(self.params_dir, f"{name}.csv")

    def _load_platform(
        self, platform: str, valid_ids: set[str]
    ) -> dict[str, Any]:
        path = self._csv_path(platform)
        if not os.path.exists(path):
            return {}

        config = self.registry.platforms[platform]
        klass  = self.registry.classes[platform]
        df     = pd.read_csv(path).fillna(value=pd.NA)
        result: dict[str, Any] = {}

        for _, row in df.iterrows():
            pid = row["param_id"]

            if pid not in valid_ids:
                print(
                    f"[WARNING] {platform}.csv: "
                    f"'{pid}' no existe en general.csv — ignorado"
                )
                continue

            kwargs: dict[str, Any] = {"param_id": pid}

            for col in config["required"]:
                kwargs[col] = row[col]

            for col, default_val in config["optional"].items():
                val = row.get(col, pd.NA)
                kwargs[col] = val if pd.notna(val) else default_val

            result[pid] = klass(**kwargs)

        return result

    def load(self) -> list[ParameterGeneral]:
        """Punto de entrada principal. Devuelve la lista completa de ParameterGeneral."""
        df_general = pd.read_csv(self._csv_path("general"), delimiter=";")
        valid_ids  = set(df_general["param_id"])

        platform_data = {
            p: self._load_platform(p, valid_ids)
            for p in self.registry.names
        }

        parameters: list[ParameterGeneral] = []

        for _, row in df_general.iterrows():
            pid   = row["param_id"]
            param = ParameterGeneral(
                param_id    = pid,
                name        = str(row["name"]),
                description = str(row["description"]),
                unit        = str(row["unit"]),
                min         = float(row["min"]),
                max         = float(row["max"]),
                default     = float(row["default"]),
            )
            param._attach_platforms(self.registry)

            for p_name, p_data in platform_data.items():
                setattr(param, p_name, p_data.get(pid))

            parameters.append(param)

        return parameters
