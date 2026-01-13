bl_info = {
    "name": "Rig Diagrams (Graphviz)",
    "author": "Fabrício + ChatGPT",
    "version": (0, 2, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Rig Diagrams",
    "description": "Gera diagramas de hierarquia (DEF/ORG/MCH) via Graphviz, com cadeia completa e ordenação .L/.R.",
    "category": "Rigging",
}

import bpy
import os
import subprocess
from collections import defaultdict
from bpy.props import EnumProperty, StringProperty
from bpy.types import Operator, Panel, AddonPreferences, PropertyGroup

ROOTS = ("DEF", "ORG", "MCH")

# ============================
# Core helpers
# ============================

def _require_armature_object(context):
    obj = context.object
    if obj is None or obj.type != "ARMATURE":
        raise RuntimeError("Selecione uma Armature antes de gerar o diagrama.")
    return obj

def _collect_collection_tree(root_coll):
    tree = set()
    def walk(c):
        tree.add(c)
        for ch in c.children:
            walk(ch)
    walk(root_coll)
    return tree

def _bones_in_collection_tree(arm_obj, root_name):
    """
    Base subset: bones que pertencem à árvore de Bone Collections root_name.
    """
    arm = arm_obj.data
    root = arm.collections.get(root_name)
    if root is None:
        return set()

    tree = _collect_collection_tree(root)
    names = set()

    for b in arm.bones:
        for c in b.collections:
            if c in tree:
                names.add(b.name)
                break
    return names

def expand_with_ancestors(arm_obj, subset):
    """
    Inclui toda a cadeia de pais (ancestors) até a raiz,
    mesmo que esses bones não pertençam à collection DEF/ORG/MCH.
    """
    bones = arm_obj.data.bones
    subset = set(subset)

    for name in list(subset):
        b = bones.get(name)
        while b and b.parent:
            p = b.parent.name
            if p in subset:
                break
            subset.add(p)
            b = b.parent
    return subset

def build_children_map(arm_obj, subset):
    """
    Mapa pai -> filhos, apenas dentro do subset.
    """
    subset = set(subset)
    children = defaultdict(list)
    for b in arm_obj.data.bones:
        if b.name not in subset:
            continue
        if b.parent and b.parent.name in subset:
            children[b.parent.name].append(b.name)
    return children

def build_edges_for_subset(children_map):
    """
    edges = children_map (mesma estrutura), separado por clareza.
    """
    return children_map

def suffix_bucket(name: str):
    """
    Ordenação vertical desejada:
      .L em cima (0)
      sem sufixo em meio (1)
      .R embaixo (2)
      outros por último (3)
    """
    if name.endswith(".L"):
        return 0
    if name.endswith(".R"):
        return 2
    # detecta outros padrões (ex: _L, -L) se quiser no futuro
    return 1

def add_invisible_order_constraints(lines, children_map):
    """
    Força ordem vertical dos filhos por pai usando:
    - rank=same para manter no mesmo nível horizontal
    - arestas invisíveis para impor ordem .L -> none -> .R
    """
    for parent, kids in children_map.items():
        if len(kids) < 2:
            continue

        ordered = sorted(kids, key=lambda n: (suffix_bucket(n), n))

        # Pré-escapa nomes (evita backslash dentro de f-string)
        escaped = []
        for k in ordered:
            esc = k.replace('"', '\\"')
            escaped.append(f"\"{esc}\";")

        # Mesmo rank
        rank_nodes = " ".join(escaped)
        lines.append(f"  {{ rank=same; {rank_nodes} }}")

        # Arestas invisíveis para impor ordem vertical
        for a, b in zip(ordered, ordered[1:]):
            aa = a.replace('"', '\\"')
            bb = b.replace('"', '\\"')
            lines.append(f'  "{aa}" -> "{bb}" [style=invis, weight=80];')

        lines.append("")

def write_dot(dot_path, title, subset, edges, children_map, dpi=240):
    """
    Gera DOT com:
    - texto grande e legível
    - fundo escuro
    - layout LR
    - ordenação vertical L/None/R
    """
    lines = []
    lines.append("digraph G {")
    lines.append(f'  graph [rankdir=LR, splines=ortho, nodesep=0.35, ranksep=0.75, bgcolor="#0f0f0f", dpi={dpi}];')

    # Fonte grande + contraste
    # DejaVu Sans costuma existir em Windows/Linux. Se quiser, pode trocar por Arial.
    lines.append('  node  [shape=box, style="rounded,filled", fillcolor="#2a2a2a", color="#b0b0b0", penwidth=1.4, fontname="DejaVu Sans", fontsize=18, fontcolor="#ffffff"];')
    lines.append('  edge  [color="#b0b0b0", penwidth=1.3, arrowsize=0.7];')

    lines.append(f'  label="{title}"; labelloc="t"; fontname="DejaVu Sans"; fontsize=22; fontcolor="#00d38a";')
    lines.append("")

    # Nós (ordem estável)
    for n in sorted(subset):
        safe = n.replace('"', '\\"')
        lines.append(f'  "{safe}";')

    lines.append("")

    # Arestas reais parent -> child
    for parent, kids in edges.items():
        p = parent.replace('"', '\\"')
        for k in sorted(kids, key=lambda n: (suffix_bucket(n), n)):
            kk = k.replace('"', '\\"')
            lines.append(f'  "{p}" ->(toggle)'.replace('(toggle)', f'"{kk}"') + ";")  # evita formatação estranha em alguns editores

    lines.append("")

    # Ordenação vertical
    add_invisible_order_constraints(lines, children_map)

    lines.append("}")

    with open(dot_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def export_graphviz_png(context, root_name, out_dir_abs, dot_exe="dot", dpi=240, include_ancestors=True):
    arm_obj = _require_armature_object(context)
    os.makedirs(out_dir_abs, exist_ok=True)

    subset = _bones_in_collection_tree(arm_obj, root_name)
    if not subset:
        raise RuntimeError(f"Não encontrei bones na árvore de Bone Collections '{root_name}'.")

    if include_ancestors:
        subset = expand_with_ancestors(arm_obj, subset)

    children_map = build_children_map(arm_obj, subset)
    edges = build_edges_for_subset(children_map)

    base = f"{arm_obj.name}_{root_name}"
    dot_path = os.path.join(out_dir_abs, f"{base}.dot")
    png_path = os.path.join(out_dir_abs, f"{base}.png")

    write_dot(dot_path, f"{root_name} hierarchy", subset, edges, children_map, dpi=dpi)

    # dot -Gdpi=240 -Tpng in.dot -o out.png
    subprocess.run([dot_exe, f"-Gdpi={dpi}", "-Tpng", dot_path, "-o", png_path], check=True)
    return png_path

def load_or_reload_image(png_path):
    name = os.path.basename(png_path)
    img = bpy.data.images.get(name)
    if img is None:
        img = bpy.data.images.load(png_path, check_existing=True)
    else:
        img.filepath = png_path
        img.reload()
    return img

def show_image_in_image_editor(context, image):
    for area in context.window.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            for space in area.spaces:
                if space.type == 'IMAGE_EDITOR':
                    space.image = image
                    return True

    # fallback: converte uma área comum em Image Editor
    for area in context.window.screen.areas:
        if area.type in {'VIEW_3D', 'TEXT_EDITOR', 'OUTLINER', 'PROPERTIES'}:
            area.type = 'IMAGE_EDITOR'
            for space in area.spaces:
                if space.type == 'IMAGE_EDITOR':
                    space.image = image
                    return True
    return False

# ============================
# Addon Preferences + Settings
# ============================

class RDGV_AddonPreferences(AddonPreferences):
    bl_idname = __name__

    dot_executable: StringProperty(
        name="Graphviz dot executable",
        description="Caminho para o executável 'dot' (ex.: dot ou C:\\Program Files\\Graphviz\\bin\\dot.exe)",
        default="dot",
        subtype='FILE_PATH'
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Graphviz configuration")
        layout.prop(self, "dot_executable")


class RDGV_Settings(PropertyGroup):
    root: EnumProperty(
        name="Root",
        description="Qual árvore gerar",
        items=[
            ("DEF", "DEF", "Gera diagrama DEF"),
            ("ORG", "ORG", "Gera diagrama ORG"),
            ("MCH", "MCH", "Gera diagrama MCH"),
            ("ALL", "ALL", "Gera DEF/ORG/MCH"),
        ],
        default="ALL"
    )

    out_dir: StringProperty(
        name="Output dir",
        description="Diretório de saída (// = pasta do .blend)",
        default="//rig_diagrams",
        subtype='DIR_PATH'
    )

    last_png: StringProperty(
        name="Last PNG",
        description="Última imagem gerada",
        default="",
        subtype='FILE_PATH'
    )

    dpi: EnumProperty(
        name="DPI",
        description="Resolução do PNG (maior = texto mais legível)",
        items=[
            ("160", "160", "Bom"),
            ("220", "220", "Melhor"),
            ("240", "240", "Ótimo (recomendado)"),
            ("300", "300", "Excelente (arquivo maior)"),
        ],
        default="240"
    )

    include_ancestors: EnumProperty(
        name="Include chain",
        description="Incluir os bones intermediários (pais) mesmo fora de DEF/ORG/MCH",
        items=[
            ("YES", "Yes", "Inclui ancestors para manter a cadeia completa"),
            ("NO", "No", "Apenas bones dentro da collection"),
        ],
        default="YES"
    )


# ============================
# Operators
# ============================

class RDGV_OT_refresh(Operator):
    bl_idname = "rdgv.refresh"
    bl_label = "Refresh diagrams"
    bl_description = "Gera PNG(s) via Graphviz e recarrega no Blender"

    def execute(self, context):
        st = context.scene.rdgv_settings

        # Preferências: se rodar como script solto, cai no default "dot"
        addon = context.preferences.addons.get(__name__)
        if addon is None:
            addon = context.preferences.addons.get("rig_diagrams_graphviz")
        dot_exe = addon.preferences.dot_executable if addon else "dot"

        out_dir_abs = bpy.path.abspath(st.out_dir)
        dpi = int(st.dpi)
        include_ancestors = (st.include_ancestors == "YES")

        try:
            if st.root == "ALL":
                last_img = None
                for r in ROOTS:
                    png = export_graphviz_png(context, r, out_dir_abs, dot_exe=dot_exe, dpi=dpi, include_ancestors=include_ancestors)
                    last_img = load_or_reload_image(png)
                    st.last_png = png
                self.report({'INFO'}, "Diagramas DEF/ORG/MCH gerados e recarregados.")
            else:
                png = export_graphviz_png(context, st.root, out_dir_abs, dot_exe=dot_exe, dpi=dpi, include_ancestors=include_ancestors)
                img = load_or_reload_image(png)
                st.last_png = png
                self.report({'INFO'}, f"Diagrama {st.root} gerado e recarregado.")

        except subprocess.CalledProcessError as e:
            self.report({'ERROR'}, f"Falha ao executar Graphviz 'dot'. Configure o caminho do 'dot'. ({e})")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        return {'FINISHED'}


class RDGV_OT_open_last(Operator):
    bl_idname = "rdgv.open_last"
    bl_label = "Open last image"
    bl_description = "Abre a última imagem gerada no Image Editor (ou cria um Image Editor)"

    def execute(self, context):
        st = context.scene.rdgv_settings
        if not st.last_png:
            self.report({'WARNING'}, "Nenhuma imagem gerada ainda. Use Refresh primeiro.")
            return {'CANCELLED'}

        png = bpy.path.abspath(st.last_png)
        if not os.path.exists(png):
            self.report({'ERROR'}, f"Arquivo não existe: {png}")
            return {'CANCELLED'}

        img = load_or_reload_image(png)
        ok = show_image_in_image_editor(context, img)
        if not ok:
            self.report({'WARNING'}, "Não consegui abrir em um Image Editor automaticamente.")
        return {'FINISHED'}


# ============================
# Panel
# ============================

class RDGV_PT_panel(Panel):
    bl_label = "Rig Diagrams (Graphviz)"
    bl_idname = "RDGV_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Rig Diagrams'

    def draw(self, context):
        layout = self.layout
        st = context.scene.rdgv_settings

        layout.prop(st, "root")
        layout.prop(st, "out_dir")
        layout.prop(st, "dpi")
        layout.prop(st, "include_ancestors")

        row = layout.row()
        row.operator("rdgv.refresh", icon="FILE_REFRESH")

        row = layout.row()
        row.operator("rdgv.open_last", icon="IMAGE_DATA")

        if st.last_png:
            layout.separator()
            layout.label(text="Last generated:")
            layout.label(text=os.path.basename(st.last_png))


# ============================
# Registration
# ============================

classes = (
    RDGV_AddonPreferences,
    RDGV_Settings,
    RDGV_OT_refresh,
    RDGV_OT_open_last,
    RDGV_PT_panel,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.rdgv_settings = bpy.props.PointerProperty(type=RDGV_Settings)

def unregister():
    del bpy.types.Scene.rdgv_settings
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
