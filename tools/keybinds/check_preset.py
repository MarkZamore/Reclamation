"""Check registration, vanilla controls, and reviewed physical-key sharing."""
from collections import defaultdict
from hashlib import sha256
import json
import re

from build_preset import HERE, PRESET, UNKNOWN, read_rows, render

VALID_KEY = re.compile(r"key\.(?:keyboard\.[a-z0-9.]+|mouse\.[a-z0-9]+)(?::(?:ALT|CONTROL|SHIFT))?")


def check():
    data = PRESET.read_bytes()
    if data != render().encode("utf-8"):
        raise ValueError("Regenerate launcher/controls-preset.txt")
    stock = read_rows(HERE / "registered.txt")
    values = read_rows(PRESET)
    vanilla = list(stock)[:34]
    if len(stock) != 232 or list(values) != list(stock) or vanilla[-1] != "key_key.hotbar.9":
        raise ValueError("Native registration inventory changed")
    groups = defaultdict(list)
    for name, value in values.items():
        if not VALID_KEY.fullmatch(value):
            raise ValueError(f"Invalid Forge mapping: {name}:{value}")
        if name in vanilla and value != stock[name]:
            raise ValueError(f"Vanilla control changed: {name}")
        if value.partition(":")[0] == UNKNOWN:
            if value != stock[name]:
                raise ValueError(f"Mapping disabled by preset: {name}")
            continue
        groups[value.partition(":")[0]].append(f"{name}:{value}")
    actual = {key: rows for key, rows in groups.items() if len(rows) > 1}
    approved = json.loads((HERE / "shared-inputs.json").read_text(encoding="utf-8"))
    if actual != approved:
        raise ValueError("Unreviewed physical-key sharing or modifier change")
    changes = sum(values[name] != stock[name] for name in stock)
    print(f"{len(values)} native mappings, {len(vanilla)} vanilla unchanged, {changes} changes")
    print(f"{len(actual)} reviewed shared inputs; SHA-256 {sha256(data).hexdigest()}")


if __name__ == "__main__":
    check()
