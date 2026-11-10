"""Valida las plantillas ARM sin necesidad de una suscripción Azure.

Revisa: JSON válido, $schema/contentVersion, recursos esperados y que cada
archivo de parámetros por ambiente coincida con los parámetros de la plantilla.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ARM_DIR = Path(__file__).parents[1] / "infra" / "arm"
EXPECTED_RESOURCES = {
    "Microsoft.Storage/storageAccounts",
    "Microsoft.Storage/storageAccounts/blobServices/containers",
}


def main() -> int:
    errors: list[str] = []
    template = json.loads((ARM_DIR / "azuredeploy.json").read_text(encoding="utf-8"))

    for key in ("$schema", "contentVersion", "parameters", "resources"):
        if key not in template:
            errors.append(f"azuredeploy.json: falta '{key}'")

    types = {r.get("type") for r in template.get("resources", [])}
    if missing := EXPECTED_RESOURCES - types:
        errors.append(f"azuredeploy.json: faltan recursos {sorted(missing)}")

    storage = next(
        (r for r in template["resources"] if r["type"] == "Microsoft.Storage/storageAccounts"),
        {},
    )
    if not storage.get("properties", {}).get("isHnsEnabled"):
        errors.append("La cuenta de almacenamiento debe tener isHnsEnabled=true (Data Lake Gen2)")

    tpl_params = template.get("parameters", {})
    required = {k for k, v in tpl_params.items() if "defaultValue" not in v}
    for env in ("dev", "test", "prod"):
        path = ARM_DIR / f"azuredeploy.parameters.{env}.json"
        if not path.exists():
            errors.append(f"Falta {path.name}")
            continue
        params = json.loads(path.read_text(encoding="utf-8")).get("parameters", {})
        if unknown := set(params) - set(tpl_params):
            errors.append(f"{path.name}: parámetros desconocidos {sorted(unknown)}")
        if absent := required - set(params):
            errors.append(f"{path.name}: faltan parámetros obligatorios {sorted(absent)}")
        if params.get("environment", {}).get("value") != env:
            errors.append(f"{path.name}: environment debe ser '{env}'")
        allowed = tpl_params.get("environment", {}).get("allowedValues", [])
        if env not in allowed:
            errors.append(f"'{env}' no está en allowedValues")

    if errors:
        print("Validación ARM FALLÓ:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("Validación ARM OK: plantilla + parámetros dev/test/prod consistentes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
