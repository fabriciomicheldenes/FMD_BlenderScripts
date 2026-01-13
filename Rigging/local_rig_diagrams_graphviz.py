import bpy
import os
import subprocess
from collections import defaultdict

# ============================
# Config
# ============================
DOT_EXE = "dot"  # ou r"C:\Program Files\Graphviz\bin\dot.exe"
OUT_DIR = "//rig_diagrams_local"
DPI = 240

# Opcional: restringir a uma raiz de Bone Collection (DEF/ORG/MCH) ou None
ROOT_FILTER = None  # "DEF" / "ORG" / "MCH" / None

# ============================
# Helpers
# ============================

def require_armature_and_active_bone():
    obj = bpy.context.object
    if obj is None or obj.type != "ARMATURE":
        raise RuntimeError("Selecione uma Armature.")
    if bpy.context.mode != "POSE":
        raise RuntimeError("Entre em Pose Mode e selecione um bone ativo.")
    active = bpy.context.active_pose_bone
    if active is None:
        raise RuntimeError("Selecione um bone ativo em Pose Mode.")
    return obj, active

def collect_collection_tree(arm_data, root_name):
    root = arm_data.collections.get(root_name)
    if root is None:
        return None, set()
    tree = set()
    def walk(c):
        tree.add(c)
        for ch in c.children:
            walk(ch)
    walk(root)
    return root, tree

def bone_in_collection_tree(arm_obj, bone_name, tree):
    b = arm_obj.data.bones.get(bone_name)
    if b is None:
        return False
    for c in b.collections:
        if c in tree:
            return True
    return False

def gv_escape(s: str) -> str:
    return s.replace('"', '\\"')

def suffix_bucket(name: str):
    if name.endswith(".L"):
        return 0
    if name.endswith(".R"):
        return 2
    return 1  # sem sufixo no meio

def add_invisible_order_constraints(lines, parent_to_children):
    """
    Força ordem vertical L -> none -> R para filhos do mesmo pai.
    """
    for parent, kids in parent_to_children.items():
        if len(kids) < 2:
            continue

        ordered = sorted(kids, key=lambda n: (suffix_bucket(n), n))

        escaped_nodes = [f"\"{gv_escape(k)}\";" for k in ordered]
        lines.append(f"  {{ rank=same; {' '.join(escaped_nodes)} }}")

        for a, b in zip(ordered, ordered[1:]):
            lines.append(f'  "{gv_escape(a)}" -> "{gv_escape(b)}" [style=invis, weight=80];')

        lines.append("")

def children_of(arm_obj, bone_data):
    return [b for b in arm_obj.data.bones if b.parent == bone_data]

def get_local_neighborhood_with_siblings(arm_obj, active_pb, root_filter=None):
    """
    Subset inclui:
    - grandparent
    - parent
    - active
    - siblings (outros filhos do mesmo parent)
    - children(active)
    - grandchildren(active)
    """
    bones = arm_obj.data.bones
    active_b = bones.get(active_pb.name)
    if active_b is None:
        raise RuntimeError("Bone ativo não encontrado em arm_obj.data.bones.")

    # filtro por collection tree (opcional)
    tree = None
    if root_filter:
        _, tree = collect_collection_tree(arm_obj.data, root_filter)
        if not tree:
            raise RuntimeError(f"Root filter '{root_filter}' não encontrada em Bone Collections.")
        def allowed(n): return bone_in_collection_tree(arm_obj, n, tree)
    else:
        def allowed(n): return True

    subset = set()

    p = active_b.parent
    gp = p.parent if p else None

    # ancestors
    for node in (gp, p, active_b):
        if node and allowed(node.name):
            subset.add(node.name)

    # siblings (inclui o próprio ativo para garantir rank/ordem)
    if p:
        sibs = children_of(arm_obj, p)
        for s in sibs:
            if allowed(s.name):
                subset.add(s.name)
    else:
        # se não tem parent, siblings não fazem sentido
        subset.add(active_b.name)

    # children e grandchildren do ativo
    kids = children_of(arm_obj, active_b)
    for ch in kids:
        if allowed(ch.name):
            subset.add(ch.name)

        gkids = children_of(arm_obj, ch)
        for gch in gkids:
            if allowed(gch.name):
                subset.add(gch.name)

    # garante ativo sempre
    subset.add(active_b.name)

    return subset

def build_edges(arm_obj, subset):
    subset = set(subset)
    parent_to_children = defaultdict(list)

    for b in arm_obj.data.bones:
        if b.name not in subset:
            continue
        if b.parent and b.parent.name in subset:
            parent_to_children[b.parent.name].append(b.name)

    return parent_to_children

def write_dot(dot_path, title, subset, edges, active_name):
    lines = []
    lines.append("digraph G {")
    lines.append(f'  graph [rankdir=LR, splines=ortho, nodesep=0.45, ranksep=0.90, bgcolor="#0f0f0f", dpi={DPI}];')
    lines.append('  edge  [color="#b0b0b0", penwidth=1.3, arrowsize=0.7];')
    lines.append('  node  [shape=box, style="rounded,filled", fillcolor="#2a2a2a", color="#b0b0b0", penwidth=1.4, fontname="DejaVu Sans", fontsize=18, fontcolor="#ffffff"];')

    # Destaca o ativo
    act = gv_escape(active_name)
    lines.append(f'  "{act}" [fillcolor="#003b2a", color="#00d38a", penwidth=2.2];')

    lines.append(f'  label="{title}"; labelloc="t"; fontname="DejaVu Sans"; fontsize=22; fontcolor="#00d38a";')
    lines.append("")

    # nós
    for n in sorted(subset):
        lines.append(f'  "{gv_escape(n)}";')

    lines.append("")

    # arestas (com ordenação por sufixo na listagem)
    for parent, kids in edges.items():
        p = gv_escape(parent)
        for k in sorted(kids, key=lambda n: (suffix_bucket(n), n)):
            lines.append(f'  "{p}" -> "{gv_escape(k)}";')

    lines.append("")
    add_invisible_order_constraints(lines, edges)
    lines.append("}")

    with open(dot_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def load_or_reload_image(png_path):
    name = os.path.basename(png_path)
    img = bpy.data.images.get(name)
    if img is None:
        img = bpy.data.images.load(png_path, check_existing=True)
    else:
        img.filepath = png_path
        img.reload()
    return img

def show_image_in_image_editor(image):
    ctx = bpy.context
    for area in ctx.window.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            for space in area.spaces:
                if space.type == 'IMAGE_EDITOR':
                    space.image = image
                    return True
    for area in ctx.window.screen.areas:
        if area.type in {'VIEW_3D', 'TEXT_EDITOR', 'OUTLINER', 'PROPERTIES'}:
            area.type = 'IMAGE_EDITOR'
            for space in area.spaces:
                if space.type == 'IMAGE_EDITOR':
                    space.image = image
                    return True
    return False

# ============================
# RUN
# ============================

arm_obj, active_pb = require_armature_and_active_bone()

out_dir_abs = bpy.path.abspath(OUT_DIR)
os.makedirs(out_dir_abs, exist_ok=True)

subset = get_local_neighborhood_with_siblings(arm_obj, active_pb, root_filter=ROOT_FILTER)
edges = build_edges(arm_obj, subset)

base = f"{arm_obj.name}_LOCAL_SIB_{active_pb.name}"
dot_path = os.path.join(out_dir_abs, f"{base}.dot")
png_path = os.path.join(out_dir_abs, f"{base}.png")

write_dot(dot_path, f"LOCAL+SIBLINGS: {active_pb.name}", subset, edges, active_pb.name)

subprocess.run([DOT_EXE, f"-Gdpi={DPI}", "-Tpng", dot_path, "-o", png_path], check=True)

img = load_or_reload_image(png_path)
show_image_in_image_editor(img)

print("[OK] Diagrama local (com siblings) gerado:", png_path)
