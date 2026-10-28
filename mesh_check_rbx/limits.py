# SPDX-License-Identifier: GPL-3.0-or-later
"""Roblox mesh limits, copied from Roblox's creator documentation.

Source: https://github.com/Roblox/creator-docs (content/en-us/...), checked
2026-10-28. Each value names the page it comes from so it can be re-checked
when Roblox changes a limit.
"""

CHECKED = "2026-10-28"

DOCS = {
    "modeling": "https://create.roblox.com/docs/art/modeling/specifications",
    "textures": "https://create.roblox.com/docs/art/modeling/texture-specifications",
    "rigid": "https://create.roblox.com/docs/avatar/rigid-accessories/specifications",
    "layered": "https://create.roblox.com/docs/avatar/layered-accessories/specifications",
    "blender": "https://create.roblox.com/docs/art/blender",
}

# Presets: triangle budget, max texture side, whether cages are required.
PRESETS = {
    # "Individual meshes can not exceed 20,000 triangles." (modeling)
    # Texture maps: "up to 1024x1024 pixel spaces" (textures).
    "MESH": {"label": "Mesh (MeshPart)", "tris": 20000, "texture": 1024, "texture_hard": False, "cages": False, "doc": "modeling"},
    # "Rigid accessories can't exceed 4k triangles." Marketplace textures
    # "cannot exceed 2048x2048 resolution." (rigid)
    "RIGID": {"label": "Rigid accessory", "tris": 4000, "texture": 2048, "texture_hard": True, "cages": False, "doc": "rigid"},
    # "Layered accessories can't exceed 4k triangles." Same texture limit;
    # "must contain an inner mesh cage and an outer mesh cage." (layered)
    "LAYERED": {"label": "Layered accessory", "tris": 4000, "texture": 2048, "texture_hard": True, "cages": True, "doc": "layered"},
}

# "A vertex can not be influenced by more than 4 bones or joints." (modeling)
MAX_INFLUENCES = 4

INNER_CAGE_SUFFIX = "_InnerCage"
OUTER_CAGE_SUFFIX = "_OuterCage"

# Rigid accessory maximum size in studs, (width X, height Y, depth Z) in
# Roblox axes, per body scale (rigid). Blender's X is width, Z is height and
# Y is depth. Sizes marked "not centered" in the docs are total extents here.
ACCESSORY_SIZES = {
    "NORMAL": {
        "HAT": (1.87, 2.5, 1.87),
        "HAIR": (1.87, 3.12, 2.18),
        "FACE": (1.87, 1.25, 1.25),
        "EYEBROW": (1.5, 0.5, 0.5),
        "NECK": (2.95, 3.68, 2.16),
        "SHOULDER_NECK": (6.90, 3.68, 3.24),
        "SHOULDER_COLLAR": (2.95, 3.68, 3.24),
        "SHOULDER": (2.67, 4.40, 3.09),
        "FRONT": (2.95, 3.68, 3.24),
        "BACK": (9.86, 8.59, 4.87),
        "WAIST": (3.94, 4.29, 7.57),
    },
    "SLENDER": {
        "HAT": (1.78, 2.5, 1.78),
        "HAIR": (1.78, 3.12, 2.08),
        "FACE": (1.78, 1.25, 1.18),
        "EYEBROW": (1.5, 0.5, 0.5),
        "NECK": (2.59, 3.39, 1.92),
        "SHOULDER_NECK": (6.05, 3.39, 2.88),
        "SHOULDER_COLLAR": (2.59, 3.39, 2.88),
        "SHOULDER": (2.37, 3.96, 2.75),
        "FRONT": (2.59, 3.39, 2.88),
        "BACK": (8.64, 7.91, 4.32),
        "WAIST": (3.76, 3.29, 6.73),
    },
    "CLASSIC": {
        "HAT": (3, 4, 3),
        "HAIR": (3, 5, 3.5),
        "FACE": (3, 2, 2),
        "EYEBROW": (1.5, 0.5, 0.5),
        "NECK": (3, 3, 2),
        "SHOULDER_NECK": (7, 3, 3),
        "SHOULDER_COLLAR": (3, 3, 3),
        "SHOULDER": (3, 3, 3),
        "FRONT": (3, 3, 3),
        "BACK": (10, 7, 4.5),
        "WAIST": (4, 3.5, 7),
    },
}

ACCESSORY_TYPE_LABELS = {
    "HAT": "Hat",
    "HAIR": "Hair",
    "FACE": "Face",
    "EYEBROW": "Eyebrow / eyelashes",
    "NECK": "Neck",
    "SHOULDER_NECK": "Shoulder (NeckAttachment)",
    "SHOULDER_COLLAR": "Shoulder (collar attachments)",
    "SHOULDER": "Shoulder (shoulder attachments)",
    "FRONT": "Front",
    "BACK": "Back",
    "WAIST": "Waist",
}

BODY_SCALE_LABELS = {"NORMAL": "Normal (Rthro)", "SLENDER": "Slender (Rthro Narrow)", "CLASSIC": "Classic"}
