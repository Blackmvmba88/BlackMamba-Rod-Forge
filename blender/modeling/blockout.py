from __future__ import annotations


def clear_scene(bpy) -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def ensure_collection(bpy, name: str):
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection


def create_named_cube(bpy, name: str, location, scale, collection_name: str = "RF_BLOCKOUT"):
    collection = ensure_collection(bpy, collection_name)
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale

    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def seed_hotrod_blockout(bpy) -> list[str]:
    """Create only the primary proportional masses for the first validation pass."""
    specs = [
        ("RF_chassis_seed", (0.0, 0.0, 0.65), (4.8, 1.7, 0.35)),
        ("RF_cabin_seed", (0.35, 0.0, 1.55), (2.1, 1.65, 1.65)),
        ("RF_engine_seed", (-1.65, 0.0, 1.05), (1.75, 1.15, 1.15)),
        ("RF_grille_seed", (-2.65, 0.0, 1.0), (0.28, 1.0, 1.55)),
    ]
    return [create_named_cube(bpy, name, loc, scale).name for name, loc, scale in specs]
