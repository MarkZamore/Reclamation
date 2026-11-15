"""Add the Reclamation controls preset to a verified pack manifest."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import zipfile

from build_preset import PACK, PRESET, render

PRESET_PATH = "launcher/controls-preset.txt"
MANIFEST = "pack-manifest.json"


def git(*args):
    return subprocess.check_output(["git", "-C", str(PACK), *args])


def pin(data):
    return {"sizeBytes": len(data), "sha256": sha256(data).hexdigest()}


def read_zip(assets, row, expected_names):
    path = assets / row["name"]
    if path.name != row["name"] or pin(path.read_bytes()) != {key: row[key] for key in ("sizeBytes", "sha256")}:
        raise ValueError(f"Invalid release asset {path.name}")
    with zipfile.ZipFile(path) as archive:
        if sorted(archive.namelist()) != sorted(expected_names):
            raise ValueError(f"Unexpected members in {path.name}")
        return {name: archive.read(name) for name in expected_names}


def write_zip(output, contents, name_for_hash):
    path = output / ".asset.zip"
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(contents.items()):
            item = zipfile.ZipInfo(name)
            item.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(item, data)
    metadata = pin(path.read_bytes())
    metadata["name"] = name_for_hash(metadata["sha256"])
    path.rename(output / metadata["name"])
    return metadata


def stage(manifest_path, assets, output):
    manifest = json.loads(manifest_path.read_bytes())
    if (manifest["packId"], manifest["minecraftVersion"], manifest["loader"]["version"]) != (
        "minecraft-21", "1.20.1", "47.4.0"
    ):
        raise ValueError("Unexpected pack or platform")
    previous = manifest["revision"]
    revision = git("rev-parse", "HEAD").decode().strip()
    changed = git("diff", "--name-only", previous, revision).decode().splitlines()
    if (previous != revision and not changed) or any(
        path not in {PRESET_PATH, "README.md", ".gitattributes", "tools/qa-public-497.json"}
        and not path.startswith("tools/keybinds/")
        for path in changed
    ):
        raise ValueError("This staging command requires a controls-only update")
    preset = PRESET.read_bytes()
    if preset != render().encode() or preset != git("show", f"{revision}:{PRESET_PATH}"):
        raise ValueError("Preset does not match its inputs or source commit")

    rows = {row["path"]: row for row in manifest["files"]}
    launcher = next(row for row in manifest["assets"] if "launcher/jvm-args.txt" in row["covers"])
    contents = read_zip(assets, launcher, launcher["covers"])
    for name, data in contents.items():
        if rows[name] != {"path": name, **pin(data)}:
            raise ValueError(f"Existing launcher asset differs from manifest for {name}")
    contents[PRESET_PATH] = preset
    rows[PRESET_PATH] = {"path": PRESET_PATH, **pin(preset)}

    library = manifest["library"]
    card = read_zip(assets, library, ("library.json", "preview.jpg"))
    metadata = json.loads(card["library.json"])
    if metadata["revision"] != previous or metadata["id"] != manifest["packId"]:
        raise ValueError("Library does not match release")
    metadata["revision"] = revision
    card["library.json"] = json.dumps(metadata, ensure_ascii=False).encode("utf-8")

    output.mkdir()
    launcher_next = write_zip(output, contents, lambda digest: f"r-{digest[:12]}-launcher.zip")
    launcher_next.update(kind="zipRoot", covers=sorted(contents))
    library_next = write_zip(output, card, lambda digest: f"library-{digest}.zip")
    library_next["revision"] = revision
    manifest["files"] = [rows[path] for path in sorted(rows)]
    manifest["assets"] = sorted(
        [row for row in manifest["assets"] if row != launcher] + [launcher_next],
        key=lambda row: row["name"],
    )
    if sorted(path for row in manifest["assets"] for path in row["covers"]) != sorted(rows):
        raise ValueError("Release assets do not cover manifest files exactly once")
    manifest["library"] = library_next
    manifest["revision"] = revision
    timestamp = int(git("show", "-s", "--format=%ct", revision))
    manifest["generatedAtUtc"] = datetime.fromtimestamp(timestamp, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (output / MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{revision} {PRESET_PATH} {rows[PRESET_PATH]['sha256']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("assets", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    stage(args.manifest, args.assets, args.output)
