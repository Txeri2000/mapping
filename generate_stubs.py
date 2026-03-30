# generate_stubs.py
"""
Genera parameters.pyi a partir de platforms.toml.
El .pyi permite autocompletado completo en VS Code, PyCharm, etc.

Uso manual:
    python generate_stubs.py
    python generate_stubs.py --config platforms.toml --out parameters.pyi

Normalmente se ejecuta automáticamente mediante el pre-commit hook
cuando platforms.toml cambia. Ver .pre-commit-config.yaml.
"""
from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

PYTHON_TYPE = {"str": "str", "float": "float", "int": "int", "bool": "bool"}


def _annotation(f: dict) -> str:
    t = PYTHON_TYPE[f["type"]]
    return f'{f["name"]}: {t}' if f["required"] else f'{f["name"]}: Optional[{t}]'


def _default(f: dict) -> str:
    if f["required"]:
        return ""
    raw = f.get("default")
    return " = None" if raw == "null" else f" = {repr(raw)}"


def _platform_class(name: str, fields: list[dict]) -> str:
    cname = f"Parameter{name.upper()}"

    attrs = ["    param_id: str"]
    for f in fields:
        attrs.append(f"    {_annotation(f)}{_default(f)}")

    init_args = ["self", "param_id: str"]
    for f in fields:
        t = PYTHON_TYPE[f["type"]]
        if f["required"]:
            init_args.append(f'{f["name"]}: {t}')
        else:
            raw = f.get("default")
            dv  = "None" if raw == "null" else repr(raw)
            init_args.append(f'{f["name"]}: Optional[{t}] = {dv}')

    return "\n".join([
        f"class {cname}:",
        *attrs,
        f"    def __init__({', '.join(init_args)}) -> None: ...",
        f"    def __repr__(self) -> str: ...",
    ])


def _general_class(platform_names: list[str]) -> str:
    base_attrs = [
        "    param_id: str",
        "    name: str",
        "    description: str",
        "    unit: str",
        "    min: float",
        "    max: float",
        "    default: float",
    ]
    plat_attrs = [
        f"    {p}: Optional[Parameter{p.upper()}]"
        for p in platform_names
    ]

    init_args = [
        "self",
        "param_id: str",
        "name: str",
        "description: str",
        "unit: str",
        "min: float",
        "max: float",
        "default: float",
        *[f"{p}: Optional[Parameter{p.upper()}] = None" for p in platform_names],
    ]

    return "\n".join([
        "class ParameterGeneral:",
        *base_attrs,
        *plat_attrs,
        f"    def __init__({', '.join(init_args)}) -> None: ...",
        "    def platforms_present(self) -> list[str]: ...",
        "    def effective_default(self, platform: str) -> float: ...",
        "    def __repr__(self) -> str: ...",
    ])


def _registry_and_loader() -> str:
    return textwrap.dedent("""\
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
            def load(self) -> list[ParameterGeneral]: ...\
    """)


# ─────────────────────────────────────────────
# Generador principal
# ─────────────────────────────────────────────

def generate(config_path: Path, out_path: Path) -> None:
    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    platforms      = raw["platforms"]
    platform_names = [p["name"] for p in platforms]

    header = textwrap.dedent(f"""\
        # AUTO-GENERATED — do not edit manually.
        # Regenerate with: python generate_stubs.py
        # Source: {config_path}

        from __future__ import annotations
        from typing import Optional, Any
    """)

    sections = [header]
    for p in platforms:
        sections.append(_platform_class(p["name"], p["fields"]))

    sections.append(_general_class(platform_names))
    sections.append(_registry_and_loader())

    out_path.write_text("\n\n".join(sections) + "\n")
    print(f"✅  Stub generado: {out_path}  ({len(platforms)} plataformas: {', '.join(platform_names)})")


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Genera parameters.pyi desde platforms.toml"
    )
    parser.add_argument(
        "--config", default="platforms.toml", type=Path,
        help="Ruta al fichero platforms.toml (default: platforms.toml)"
    )
    parser.add_argument(
        "--out", default="parameters.pyi", type=Path,
        help="Ruta de salida del stub (default: parameters.pyi)"
    )
    args = parser.parse_args()
    generate(args.config, args.out)
