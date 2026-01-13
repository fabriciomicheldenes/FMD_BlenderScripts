import bpy
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import StringProperty, PointerProperty

# Estrutura para armazenar dados hierárquicos
def get_hierarchy(obj):
    hierarchy = {}
    if obj and obj.vertex_groups:
        for vg in obj.vertex_groups:
            parts = vg.name.split('/')
            current = hierarchy
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]
    return hierarchy

# Operador para criar nova "coleção" (vertex group hierárquico)
class OBJECT_OT_CreateVertexCollection(Operator):
    bl_idname = "object.create_vertex_collection"
    bl_label = "Criar Coleção"
    bl_options = {'REGISTER', 'UNDO'}

    path: StringProperty(
        name="Caminho",
        description="Caminho da coleção (ex: 'Rig/Arm')",
        default=""
    )

    def execute(self, context):
        obj = context.active_object
        if not obj:
            self.report({'ERROR'}, "Nenhum objeto selecionado")
            return {'CANCELLED'}

        if not self.path:
            self.report({'ERROR'}, "Caminho inválido")
            return {'CANCELLED'}

        # Cria vertex groups hierárquicos
        parts = self.path.split('/')
        current_name = ""
        for part in parts:
            current_name += part if not current_name else f"/{part}"
            if current_name not in obj.vertex_groups:
                obj.vertex_groups.new(name=current_name)

        self.report({'INFO'}, f"Coleção '{self.path}' criada")
        return {'FINISHED'}

# Painel para exibir hierarquia
class DATA_PT_VertexCollections(Panel):
    bl_label = "Vertex Collections"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    def draw(self, context):
        layout = self.layout
        obj = context.object

        # Caixa de entrada para novo caminho
        row = layout.row()
        row.prop(context.scene.vertex_collection_props, "path", text="")
        row.operator("object.create_vertex_collection", text="", icon='ADD')

        # Exibir hierarquia
        if obj and obj.vertex_groups:
            hierarchy = get_hierarchy(obj)
            self.draw_hierarchy(layout, hierarchy)

    def draw_hierarchy(self, layout, hierarchy, level=0):
        for key in sorted(hierarchy.keys()):
            row = layout.row()
            row.label(text=key, icon='FILE_FOLDER' if hierarchy[key] else 'DOT')

            # Recursão para subpastas
            if hierarchy[key]:
                box = layout.box()
                self.draw_hierarchy(box, hierarchy[key], level + 1)

# Propriedades globais
class VertexCollectionProps(PropertyGroup):
    path: StringProperty(name="Caminho")

def register():
    bpy.utils.register_class(OBJECT_OT_CreateVertexCollection)
    bpy.utils.register_class(DATA_PT_VertexCollections)
    bpy.utils.register_class(VertexCollectionProps)
    bpy.types.Scene.vertex_collection_props = PointerProperty(type=VertexCollectionProps)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_CreateVertexCollection)
    bpy.utils.unregister_class(DATA_PT_VertexCollections)
    bpy.utils.unregister_class(VertexCollectionProps)
    del bpy.types.Scene.vertex_collection_props

if __name__ == "__main__":
    register()