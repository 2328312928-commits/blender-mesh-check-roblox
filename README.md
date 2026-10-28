# Mesh Check for Roblox (Blender add-on)

Checks your meshes against **Roblox's import limits** before you export, so Studio or the Marketplace doesn't reject them later. Every limit comes from Roblox's own [creator documentation](https://github.com/Roblox/creator-docs) and was last checked on **2026-10-28**. Each issue has a ? button that opens the Roblox page the rule comes from.

Works in Blender 4.2 and later; tested in Blender 5.2.

## What it checks

| Check | Rule (Roblox docs) | Level |
|---|---|---|
| Triangle budget | 20,000 per mesh; 4,000 for rigid and layered accessories. Counted after modifiers, as exported | Error |
| Accessory size | Max size in studs per accessory type (hat, hair, face, neck, shoulder, front, back, waist) and body scale (Normal, Slender, Classic) | Error |
| Zero thickness | Meshes must have volume | Error |
| Bone influences | At most 4 bones per vertex | Error |
| Cages | Layered accessories need `Name_InnerCage` and `Name_OuterCage`; stray cages are flagged | Error / warning |
| Texture size | Accessory textures max 2048×2048 (Marketplace); texture maps above 1024 are flagged for meshes | Error / warning |
| Watertight | No open edges or non-manifold edges | Warning |
| N-gons | Quads where possible | Warning |
| UVs | A UV map exists, only one UV set, all UVs inside 0–1 | Warning |
| Materials | One material per mesh | Warning |
| Transforms | Unapplied rotation or scale | Warning |
| Scene units | Unit System None, so 1 Blender unit = 1 stud | Warning |

## Install

1. Download `mesh_check_rbx-1.0.0.zip` from [Releases](../../releases).
2. In Blender: **Edit → Preferences → Get Extensions**, then the ⌄ menu → **Install from Disk...**, and pick the zip.
3. Open the 3D Viewport sidebar (**N**) → **Roblox** tab, choose the asset type and click **Check for Roblox**.

## Pro edition

**Mesh Check Pro** (coming soon to [Kettlewick Tools on Gumroad](https://kettlewick.gumroad.com)) adds:

- **One-click fixes**: apply rotation/scale (keeps children in place), triangulate only the n-gons, limit bone influences to 4 and re-normalize, remove extra UV maps, set stud units, scale oversized textures down. Or **Fix all** at once.
- **Export FBX for Roblox**: the settings from Roblox's export guide (Path Mode Copy, embedded textures, FBX unit scale, no leaf bones, no baked animation). Cages and armatures are included automatically.
- **Reports** as Markdown or JSON.
- **Command line for CI**: `blender -b model.blend --python cli.py -- --preset RIGID --fix --json report.json --export out.fbx`, which exits 1 if any error remains.
- 22 automated tests that run in real Blender, including an FBX export and re-import round trip.

The Pro edition is GPL too, as all Blender add-ons must be. Buying it pays for the extra tools, fixes when Roblox changes a limit, and support.

## Run the tests

```bash
pip install bpy==5.2.3   # Blender as a Python module (Python 3.13)
python tests/test_checks.py
```

## License and disclosure

GPL-3.0-or-later (see `LICENSE`). Not affiliated with or endorsed by Roblox Corporation. Built with the help of an AI coding assistant, then tested in real Blender as described above.

More free Roblox tools: [simulator pacing calculator](https://2328312928-commits.github.io/roblox-luau-skill/), [DataStore limits](https://2328312928-commits.github.io/roblox-luau-skill/datastore-limits/), [egg odds checker](https://2328312928-commits.github.io/roblox-luau-skill/odds/).
