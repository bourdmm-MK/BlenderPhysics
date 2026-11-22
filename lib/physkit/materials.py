"""Simple named materials, reused across models."""

import bpy

# A small shared palette so all models look like one family.
PALETTE = {
    "metal": ((0.75, 0.76, 0.78, 1), 1.0, 0.25),
    "dark_metal": ((0.15, 0.15, 0.17, 1), 1.0, 0.35),
    "wood": ((0.45, 0.28, 0.15, 1), 0.0, 0.6),
    "string": ((0.9, 0.88, 0.8, 1), 0.0, 0.8),
    "red": ((0.8, 0.1, 0.08, 1), 0.0, 0.35),
    "blue": ((0.1, 0.3, 0.8, 1), 0.0, 0.35),
    "floor": ((0.6, 0.6, 0.62, 1), 0.0, 0.9),
}


def material(name: str, color=None, metallic=None, roughness=None):
    """Return a material by name, creating it from PALETTE (or given values)."""
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    base, met, rough = PALETTE.get(name, ((0.8, 0.8, 0.8, 1), 0.0, 0.5))
    color = color or base
    metallic = met if metallic is None else metallic
    roughness = rough if roughness is None else roughness

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    # Colour shown in the quick preview (Workbench) mode too.
    mat.diffuse_color = color
    return mat


def assign(obj, mat):
    """Give an object a single material."""
    obj.data.materials.clear()
    obj.data.materials.append(mat)
