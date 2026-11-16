"""Add the pack-owned controls and multiplayer menu assets to a verified release."""
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
WARNING_JAR = "mods/reclamation-multiplayer-1.0.0.jar"
WARNING_ID = "reclamation_multiplayer"
WARNING_POLICY = "tools/multiplayer-warning/policy.json"


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


def warning_policy(revision):
    policy = json.loads(git("show", f"{revision}:{WARNING_POLICY}"))
    if policy["path"] != WARNING_JAR:
        raise ValueError("Unexpected multiplayer policy path")
    return policy


def verify_warning(manifest, assets, policy_revision=None):
    policy = warning_policy(policy_revision or manifest["revision"])
    if any(manifest[key] != policy[key] for key in ("minecraftVersion", "loader")):
        raise ValueError("Review the multiplayer warning policy for the new platform")
    expected = {key: policy[key] for key in ("path", "sizeBytes", "sha256")}
    files = [row for row in manifest["files"] if row["path"] == WARNING_JAR]
    if files != [expected]:
        raise ValueError("Release is missing its pinned multiplayer warning policy")
    matches = [row for row in manifest["assets"] if WARNING_JAR in row["covers"]]
    if len(matches) != 1 or matches[0]["covers"] != [WARNING_JAR]:
        raise ValueError("Release must supply one dedicated multiplayer policy asset")
    contents = read_zip(assets, matches[0], [WARNING_JAR])
    if pin(contents[WARNING_JAR]) != {key: expected[key] for key in ("sizeBytes", "sha256")}:
        raise ValueError("Release multiplayer warning helper differs from the fixed policy")


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
        path not in {PRESET_PATH, WARNING_JAR, "README.md", ".gitattributes", "tools/qa-public-497.json",
                     "library/loaded-mods.json", "library/mod-pages.json", "tools/prepare_release.py"}
        and not path.startswith(("tools/keybinds/", "tools/multiplayer-warning/"))
        for path in changed
    ):
        raise ValueError("This staging command requires a pack-owned controls or multiplayer update")
    preset = PRESET.read_bytes()
    if preset != render().encode() or preset != git("show", f"{revision}:{PRESET_PATH}"):
        raise ValueError("Preset does not match its inputs or source commit")

    policy = warning_policy(revision)
    if any(manifest[key] != policy[key] for key in ("minecraftVersion", "loader")):
        raise ValueError("Review the multiplayer warning policy for the new platform")
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
    warning = (PACK / WARNING_JAR).read_bytes()
    if warning != git("show", f"{revision}:{WARNING_JAR}"):
        raise ValueError("Multiplayer helper differs from the source commit")
    if pin(warning) != {key: policy[key] for key in ("sizeBytes", "sha256")}:
        raise ValueError("Source JAR differs from the fixed multiplayer warning policy")
    pages = json.loads(git("show", f"{revision}:library/mod-pages.json"))
    old_count = sum(row["isLoadedMod"] for row in metadata["mods"])
    if old_count != manifest["modCount"]:
        raise ValueError("Old release mod count does not match its library")
    metadata["mods"] = [row for row in metadata["mods"] if row["id"] != WARNING_ID]
    metadata["mods"].append({
        "id": WARNING_ID, "name": policy["name"], "version": policy["version"],
        "isLoadedMod": True, "websiteUrl": pages[WARNING_ID], "websiteAvailable": True,
        "parentId": None, "isLibrary": False,
    })
    manifest["modCount"] = sum(row["isLoadedMod"] for row in metadata["mods"])
    rows[WARNING_JAR] = {"path": WARNING_JAR, **pin(warning)}
    card["library.json"] = json.dumps(metadata, ensure_ascii=False).encode("utf-8")

    output.mkdir()
    launcher_next = write_zip(output, contents, lambda digest: f"r-{digest[:12]}-launcher.zip")
    launcher_next.update(kind="zipRoot", covers=sorted(contents))
    warning_next = write_zip(output, {WARNING_JAR: warning},
                             lambda digest: f"r-{digest[:12]}-mods.reclamation-multiplayer.zip")
    warning_next.update(kind="zipRoot", covers=[WARNING_JAR])
    library_next = write_zip(output, card, lambda digest: f"library-{digest}.zip")
    library_next["revision"] = revision
    manifest["files"] = [rows[path] for path in sorted(rows)]
    manifest["assets"] = sorted(
        [row for row in manifest["assets"] if row != launcher and WARNING_JAR not in row["covers"]]
        + [launcher_next, warning_next],
        key=lambda row: row["name"],
    )
    if sorted(path for row in manifest["assets"] for path in row["covers"]) != sorted(rows):
        raise ValueError("Release assets do not cover manifest files exactly once")
    manifest["library"] = library_next
    manifest["revision"] = revision
    timestamp = int(git("show", "-s", "--format=%ct", revision))
    manifest["generatedAtUtc"] = datetime.fromtimestamp(timestamp, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    verify_warning(manifest, output)
    (output / MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{revision} {PRESET_PATH} {rows[PRESET_PATH]['sha256']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("assets", type=Path)
    parser.add_argument("output", type=Path, nargs="?")
    parser.add_argument("--verify-warning", action="store_true")
    args = parser.parse_args()
    if args.verify_warning:
        verify_warning(json.loads(args.manifest.read_bytes()), args.assets, policy_revision="HEAD")
        print("Verified pinned multiplayer warning policy in release")
    elif args.output is None:
        parser.error("output is required when staging")
    else:
        stage(args.manifest, args.assets, args.output)
