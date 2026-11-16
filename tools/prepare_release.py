"""Stage the full Reclamation release, including the permanent pack policies."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

PACK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PACK / "tools/keybinds"))
from stage_release import MANIFEST, git, stage, verify_warning


def prepare_release(launcher, author_stage, output, include_optional=()):
    if output.exists():
        raise ValueError("Use a new output directory")
    revision = git("rev-parse", "HEAD").decode().strip()
    normal_tool = launcher / "tools/PackData/CurseForge/stage_release.py"
    with TemporaryDirectory(prefix=".reclamation-release-", dir=output.parent) as workspace:
        workspace = Path(workspace)
        base = workspace / "base"
        optional_args = [value for path in include_optional for value in ("--include-optional", path)]
        subprocess.run([
            sys.executable, "-B", str(normal_tool), "--pack-source", str(PACK),
            "--stage", str(author_stage), "--output", str(base),
            "--revision", revision, "--id", "minecraft-21", *optional_args,
        ], check=True)
        changed = workspace / "changed"
        stage(base / MANIFEST, base / "assets", changed)
        manifest = json.loads((changed / MANIFEST).read_bytes())
        final_assets = workspace / "release/assets"
        final_assets.mkdir(parents=True)
        for entry in [*manifest["assets"], manifest["library"]]:
            name = entry["name"]
            generated = changed / name
            source = generated if generated.is_file() else base / "assets" / name
            source.rename(final_assets / name)
        verify_warning(manifest, final_assets)
        (changed / MANIFEST).rename(final_assets.parent / MANIFEST)
        final_assets.parent.rename(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lanminecraft", type=Path, required=True)
    parser.add_argument("--author-stage", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--include-optional", action="append", default=[])
    args = parser.parse_args()
    prepare_release(args.lanminecraft, args.author_stage, args.output, args.include_optional)
