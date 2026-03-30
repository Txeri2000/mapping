# Copilot Instructions — param_loader

## Project purpose
Automate the loading and parameterization of simulation models across multiple platforms
(PSSE, PSCAD, PF, TSAT, EMTP). The core idea is to maintain a single source of truth
for parameters and map them to each platform's specific requirements.

---

## Architecture

### Source of truth
- `platforms.toml` — declares all simulation platforms and their fields.
  Only developers edit this file. Adding a new platform = adding a `[[platforms]]` block here.
- `params/general.csv` — master parameter table (edited by the full team, including non-technical).
- `params/<platform>.csv` — one CSV per platform, referencing `param_id` from `general.csv`.

### Key files
| File | Role | Who edits |
|---|---|---|
| `platforms.toml` | Platform definitions | Developers only |
| `parameters.py` | Runtime logic | Developers only |
| `parameters.pyi` | IDE stub — **never edit manually** | Auto-generated |
| `generate_stubs.py` | Generates `parameters.pyi` from `platforms.toml` | Run automatically |
| `validate_params.py` | Validates referential integrity between CSVs | Run automatically |
| `params/general.csv` | Master parameter list | All team |
| `params/<platform>.csv` | Platform-specific parameters | All team |

---

## Data model

### `ParameterGeneral`
Represents a parameter in a platform-agnostic way.

```python
@dataclass
class ParameterGeneral:
    param_id:    str       # unique key, shared across all CSVs
    name:        str
    description: str
    unit:        str
    min:         float
    max:         float
    default:     float
    # One optional attribute per platform (None if not present):
    psse:  Optional[ParameterPSSE]
    pscad: Optional[ParameterPSCAD]
    pf:    Optional[ParameterPF]
    tsat:  Optional[ParameterTSAT]
    emtp:  Optional[ParameterEMTP]
```

Key methods:
- `platforms_present() -> list[str]` — returns the platforms where this parameter is defined.
- `effective_default(platform: str) -> float` — returns `default_override` if set on the
  platform-specific instance, otherwise the general `default`.

### Platform-specific classes (`ParameterPSSE`, `ParameterPSCAD`, etc.)
Generated dynamically at runtime via `make_dataclass` using the field definitions in
`platforms.toml`. Always contain `param_id` plus the fields declared for that platform.
Common optional fields: `scale_factor` (default 1.0), `default_override` (default None).

### `PlatformRegistry`
Reads `platforms.toml` at startup and generates all platform-specific classes dynamically.
Single instance owned by `ParameterLoader`. Never instantiate directly.

### `ParameterLoader`
Entry point. Call `loader.load()` to get `list[ParameterGeneral]`.

```python
from parameters import ParameterLoader
loader = ParameterLoader(params_dir="params", config_path="platforms.toml")
params = loader.load()
```

---

## Invariants — never break these

- Every `param_id` in any `params/<platform>.csv` **must** exist in `params/general.csv`.
  Orphan rows are logged as warnings and skipped, never raise exceptions.
- `parameters.pyi` is always auto-generated. **Never edit it manually.**
  Regenerate with `python generate_stubs.py` or let the pre-commit hook do it.
- Platform classes are generated at runtime — do not add `ParameterPSSE` etc. as static
  classes in `parameters.py`. All platform class definitions live in `platforms.toml`.
- `ParameterGeneral` is a `@dataclass`. Platform attributes are attached dynamically via
  `_attach_platforms()` after construction; they do not appear in `__init__`.

---

## Adding a new platform

1. Add a `[[platforms]]` block to `platforms.toml` with the platform's fields.
2. Create `params/<platform_name>.csv` with at least a `param_id` column.
3. Commit — the pre-commit hook regenerates `parameters.pyi` automatically.
4. No changes to `parameters.py` are needed.

---

## Pre-commit hooks (`.pre-commit-config.yaml`)

| Hook | Trigger | Action |
|---|---|---|
| `generate-stubs` | `platforms.toml` changes | Runs `generate_stubs.py`, adds `parameters.pyi` to the commit |
| `validate-params` | Any `params/*.csv` changes | Runs `validate_params.py`, fails commit if orphan `param_id`s found |

Install: `pip install pre-commit && pre-commit install`

---

## Coding conventions

- All classes use `@dataclass` (not plain classes, not Pydantic — no external dependencies
  beyond `pandas`).
- Type hints everywhere. Use `Optional[T]` for nullable fields, not `T | None`
  (the codebase targets Python 3.10+).
- `TYPE_MAP` in `parameters.py` is the single place that maps TOML type strings
  (`"str"`, `"float"`, etc.) to Python types. Extend it there if new types are needed.
- CSV loading uses `pandas`. Empty cells are read as `pd.NA` and converted to the
  field's declared default value.
- No logging framework — use `print("[WARNING] ...")` for non-fatal issues,
  `sys.exit(1)` for fatal validation errors.

---

## What is NOT implemented yet (known gaps)

- **GitLab CI integration** — validation runs locally via pre-commit but there is no
  `.gitlab-ci.yml` yet.
- **Type validation on CSV load** — malformed values (e.g. `"1,2"` instead of `"1.2"`)
  will raise a generic pandas/Python error. A typed validation layer is not yet in place.
- **`effective_default()` on `ParameterGeneral`** — implemented, but the automation
  scripts that consume the parameter list have not been written yet.
