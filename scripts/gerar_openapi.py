"""Gera o snapshot OpenAPI do runtime para comparação versionada."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.main import criar_app

DESTINO = Path(__file__).parents[1] / "docs" / "openapi.json"


def gerar() -> str:
    esquema = criar_app().openapi()
    return json.dumps(esquema, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main() -> None:
    DESTINO.write_text(gerar(), encoding="utf-8", newline="\n")
    print(f"OpenAPI gravada em {DESTINO}")


if __name__ == "__main__":
    main()
