"""Render the Reclamation controls preset from the recorded native options."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACK = HERE.parent.parent
PRESET = PACK / "launcher/controls-preset.txt"
UNKNOWN = "key.keyboard.unknown"


def read_rows(path):
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        name, sep, key = line.partition(":")
        if not sep or not name.startswith("key_") or not key.startswith("key.") or name in rows:
            raise ValueError(f"{path.name}: invalid or duplicate mapping {line!r}")
        rows[name] = key
    return rows


def layout():
    stock = read_rows(HERE / "registered.txt")
    overrides = read_rows(HERE / "layout.txt")
    if missing := overrides.keys() - stock.keys():
        raise ValueError(f"Unregistered mappings: {sorted(missing)}")
    return stock | overrides


def render():
    return "# Reclamation 2.3.2 | Minecraft 1.20.1 | Forge 47.4.0\n" + "".join(
        f"{name}:{value}\n" for name, value in layout().items()
    )


if __name__ == "__main__":
    PRESET.write_bytes(render().encode("utf-8"))
