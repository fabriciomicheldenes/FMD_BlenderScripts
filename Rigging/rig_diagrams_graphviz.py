bl_info = {
    "name": "Rig Diagrams (Graphviz)",
    "author": "Fabrício + ChatGPT",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Rig Diagrams",
    "description": "Gera diagramas de hierarquia (DEF/ORG/MCH) via Graphviz e recarrega PNG no Blender.",
    "category": "Rigging",
}

import bpy
import os
import subprocess
from collections import defaultdict
from bpy.props import EnumProperty, StringProperty
from bpy.types import Operator, Panel, AddonPreferences, PropertyGroup


# ----------------------------
# Core: DOT/PNG export
# ----------------------------

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

def _build_edges_for_subset(arm_obj, subset_names):
    bones = arm_obj.data.bones
    subset = set(subset_names)
    children_map = defaultdict(list)

    for b in bones:
        if b.name not in subset:
            continue
        if b.parent and b.parent.name in subset:
            children_map[b.parent.name].append(b.name)

    return children_map

def _write_dot(dot_path, title, subset, edges):
    lines = []
    lines.append('digraph G {')
    lines.append('  graph [rankdir=LR, splines=ortho, nodesep=0.35, ranksep=0.65, bgcolor="#111111"];')
    lines.append('  node  [shape=box, style="rounded,filled", fillcolor="#2b2b2b", color="#7a7a7a", fontname="Inter", fontsize=12, fontcolor="#e6e6e6"];')
    lines.append('  edge  [color="#7a7a7a", penwidth=1.2, arrowsize=0.7];')
    lines.append(f'  label="{title}"; labelloc="t"; fontname="Inter"; fontsize=16; fontcolor="#00d38a";')
    lines.append("")

    for n in sorted(subset):
        safe = n.replace('"', '\\"')
        lines.append(f'  "{safe}";')

    lines.append("")

    for parent, kids in edges.items():
        p = parent.replace('"', '\\"')
        for k in sorted(kids):
            kk = k.replace('"', '\\"')
            lines.append(f'  "{p}" -> "{kk}";')

    lines.append("}")

    with open(dot_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def export_graphviz_png(context, root_name, out_dir_abs, dot_exe="dot"):
    arm_obj = _require_armature_object(context)

    os.makedirs(out_dir_abs, exist_ok=True)

    subset = _bones_in_collection_tree(arm_obj, root_name)
    if not subset:
        raise RuntimeError(f"Não encontrei bones na árvore de Bone Collections '{root_name}'.")

    edges = _build_edges_for_subset(arm_obj, subset)

    base = f"{arm_obj.name}_{root_name}"
    dot_path = os.path.join(out_dir_abs, f"{base}.dot")
    png_path = os.path.join(out_dir_abs, f"{base}.png")
    print(png_path)

    _write_dot(dot_path, f"{root_name} hierarchy", subset, edges)

    # Graphviz -> PNG
    # dot -Tpng input.dot -o output.png
    subprocess.run([dot_exe, "-Tpng", dot_path, "-o", png_path], check=True)

    return png_path


def load_or_reload_image(png_path):
    # Usa nome consistente para evitar criar várias imagens duplicadas
    name = os.path.basename(png_path)

    img = bpy.data.images.get(name)
    if img is None:
        img = bpy.data.images.load(png_path, check_existing=True)
    else:
        # garante que aponta para este arquivo e recarrega
        img.filepath = png_path
        img.reload()

    return img


def show_image_in_image_editor(context, image):
    # Tenta achar uma área Image Editor e setar a imagem nela.
    # Se não existir, troca a primeira área encontrada para IMAGE_EDITOR.
    for area in context.window.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            for space in area.spaces:
                if space.type == 'IMAGE_EDITOR':
                    space.image = image
                    return True

    # fallback: converter uma área qualquer em Image Editor
    for area in context.window.screen.areas:
        if area.type in {'VIEW_3D', 'TEXT_EDITOR', 'OUTLINER', 'PROPERTIES'}:
            area.type = 'IMAGE_EDITOR'
            for space in area.spaces:
                if space.type == 'IMAGE_EDITOR':
                    space.image = image
                    return True

    return False


# ----------------------------
# Addon preferences + settings
# ----------------------------

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


# ----------------------------
# Operators
# ----------------------------

class RDGV_OT_refresh(Operator):
    bl_idname = "rdgv.refresh"
    bl_label = "Refresh diagrams"
    bl_description = "Gera PNG(s) via Graphviz e recarrega no Blender"

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        st = context.scene.rdgv_settings

        out_dir_abs = bpy.path.abspath(st.out_dir)
        dot_exe = prefs.dot_executable

        try:
            if st.root == "ALL":
                last_img = None
                for r in ("DEF", "ORG", "MCH"):
                    png = export_graphviz_png(context, r, out_dir_abs, dot_exe=dot_exe)
                    last_img = load_or_reload_image(png)
                    st.last_png = png
                self.report({'INFO'}, "Diagramas DEF/ORG/MCH gerados e recarregados.")
            else:
                png = export_graphviz_png(context, st.root, out_dir_abs, dot_exe=dot_exe)
                img = load_or_reload_image(png)
                st.last_png = png
                self.report({'INFO'}, f"Diagrama {st.root} gerado e recarregado.")

        except subprocess.CalledProcessError as e:
            self.report({'ERROR'}, f"Falha ao executar Graphviz dot. Configure o caminho do 'dot'. ({e})")
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


# ----------------------------
# Panel
# ----------------------------

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

        row = layout.row()
        row.operator("rdgv.refresh", icon="FILE_REFRESH")

        row = layout.row()
        row.operator("rdgv.open_last", icon="IMAGE_DATA")

        if st.last_png:
            layout.separator()
            layout.label(text="Last generated:")
            layout.label(text=os.path.basename(st.last_png))


# ----------------------------
# Registration
# ----------------------------

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
