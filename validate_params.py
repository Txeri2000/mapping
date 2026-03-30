# validate_params.py
"""
Valida la integridad referencial entre general.csv y los CSVs de plataforma.
Comprueba que todo param_id de una plataforma existe en general.csv.

Uso:
    python validate_params.py
    python validate_params.py --params-dir params --config platforms.toml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

try:
    import tomllib
except ImportError:
    import tomli as tomllib


def validate(params_dir: Path, config_path: Path) -> bool:
    # Cargar IDs generales
    general_path = params_dir / "general.csv"
    if not general_path.exists():
        print(f"❌  No se encuentra {general_path}")
        return False

    general_ids = set(pd.read_csv(general_path)["param_id"])

    # Cargar nombres de plataformas desde platforms.toml
    with open(config_path, "rb") as f:
        raw = tomllib.load(f)
    platform_names = [p["name"] for p in raw["platforms"]]

    errors: list[str] = []

    for platform in platform_names:
        path = params_dir / f"{platform}.csv"
        if not path.exists():
            print(f"[INFO] {platform}.csv no encontrado — plataforma no declarada aún, OK")
            continue

        df = pd.read_csv(path)

        if "param_id" not in df.columns:
            errors.append(f"[{platform}] Falta columna 'param_id'")
            continue

        orphans = set(df["param_id"]) - general_ids
        if orphans:
            errors.append(
                f"[{platform}] param_ids sin entrada en general.csv: {sorted(orphans)}"
            )

        duplicates = df[df.duplicated("param_id")]["param_id"].tolist()
        if duplicates:
            errors.append(
                f"[{platform}] param_ids duplicados: {duplicates}"
            )

    if errors:
        print("❌  Errores de validación encontrados:\n")
        for e in errors:
            print(f"   {e}")
        return False

    print(f"✅  Validación OK — {len(general_ids)} parámetros generales, {len(platform_names)} plataformas")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Valida integridad referencial entre general.csv y CSVs de plataforma"
    )
    parser.add_argument(
        "--params-dir", default="params", type=Path,
        help="Directorio con los CSVs (default: params)"
    )
    parser.add_argument(
        "--config", default="platforms.toml", type=Path,
        help="Ruta a platforms.toml (default: platforms.toml)"
    )
    args = parser.parse_args()

    ok = validate(args.params_dir, args.config)
    sys.exit(0 if ok else 1)
