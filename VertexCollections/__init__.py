# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import bpy
import uuid
import json
from typing import Dict, List

bl_info = {
    "name": "Vertex Collection",
    "author": "Fabricio Michel Denes",
    "description": "Organiza Vertex Groups em pastas hierárquicas",
    "blender": (4, 3, 0),
    "version": (0, 2, 0),
    "location": "Properties -> Data -> Vertex Collections",
    "warning": "",
    "category": "Object",
}

def generate_uuid() -> str:
    return str(uuid.uuid4())

def get_hierarchy_dict(obj) -> Dict:
    """Convert the stored JSON string to a dictionary"""
    try:
        return json.loads(obj.folder_hierarchy.hierarchy)
    except:
        return {}

def get_expandedHierarchy_dict(obj) -> Dict:
    """Convert the stored JSON string to a dictionary"""
    try:
        return json.loads(obj.folder_hierarchy.expanded)
    except:
        return {}
    
def set_hierarchy(obj, new_dict):
    """Atualiza o JSON armazenado com um novo dicionário"""
    obj.folder_hierarchy.hierarchy = json.dumps(new_dict)
    
def generate_hierarchical_name(obj, parent_item) -> str:
    """Generates the next hierarchical name based on parent's suffix"""
    if not parent_item:  # Root level item
        # Encontrar o maior número de item raiz
        root_numbers = []
        for item in obj.VCollection:
            if not item.parent_uuid:  # Itens no nível raiz
                try:
                    num = int(item.name.split()[1])
                    root_numbers.append(num)
                except (IndexError, ValueError):
                    continue
        next_num = max(root_numbers, default=0) + 1
        return f"Item {next_num}"
    else:
        # Obter o sufixo do pai (parte após "Item ")
        parent_name_parts = parent_item.name.split()
        if len(parent_name_parts) < 2:
            parent_suffix = ""
        else:
            parent_suffix = parent_name_parts[1]

        # Encontrar o maior número entre os irmãos com o mesmo pai
        sibling_numbers = []
        for item in obj.VCollection:
            if item.parent_uuid == parent_item.uuid:
                # Dividir o sufixo do item e pegar a última parte como número
                item_suffix_parts = item.name.split()
                if len(item_suffix_parts) < 2:
                    continue
                item_suffix = item_suffix_parts[1]
                suffix_parts = item_suffix.split('_')
                try:
                    last_part = suffix_parts[-1]
                    num = int(last_part)
                    sibling_numbers.append(num)
                except (ValueError, IndexError):
                    continue

        next_num = max(sibling_numbers, default=0) + 1
        new_suffix = f"{parent_suffix}_{next_num}"
        return f"Item {new_suffix}"

class VertexCollectionItem(bpy.types.PropertyGroup):
    """Item da coleção que pode ser pasta ou grupo de vértices"""
    type: bpy.props.EnumProperty(
        items=[
            ('FOLDER', "Folder", "Pasta para organização"),
            ('GROUP', "Group", "Grupo de vértices"),
        ],
        default='FOLDER'
    ) # type: ignore
    name: bpy.props.StringProperty(name="Name", default="New Item") # type: ignore
    is_expanded: bpy.props.BoolProperty(name="Expanded", default=False) # type: ignore
    is_visible: bpy.props.BoolProperty(name="Visible", default=True) # type: ignore
    uuid: bpy.props.StringProperty(name="UUID", default="None") # type: ignore
    parent_uuid: bpy.props.StringProperty(name="UUID", default="None") # type: ignore
    depth: bpy.props.IntProperty(name="Depth", default=0) # type: ignore
    group_name: bpy.props.StringProperty(name="Vertex Group") # type: ignore

class VertexCollectionHierarchy(bpy.types.PropertyGroup):
    """Stores the hierarchical structure using UUIDs"""
    hierarchy: bpy.props.StringProperty(default=json.dumps({})) # type: ignore
    expanded: bpy.props.StringProperty(default=json.dumps({})) # type: ignore

        
def register_properties():
    if not hasattr(bpy.types.Object, "VCollection"):
        # Depois registramos as propriedades
        bpy.types.Object.VCollection = bpy.props.CollectionProperty(
            name="vFolder",
            type=VertexCollectionItem
        )
        bpy.types.Object.folder_hierarchy = bpy.props.PointerProperty(
            type=VertexCollectionHierarchy
        )
        bpy.types.Object.VCollection_index = bpy.props.IntProperty(
            name="Index",
            default=-1
        )


class DATA_UL_vertex_collections(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)

        # Indentação hierárquica
        for _ in range(item.depth):
            row.separator()
            row.separator()

        # Ícone e comportamento para pastas
        if item.type == 'FOLDER':
            # has_children = any(child.parent_uuid ==
            #                    index for child in data.VCollection)
            expand_icon = 'DOWNARROW_HLT' if item.is_expanded else 'RIGHTARROW'

            # Botão de expansão
            op = row.operator("vertex_collection.toggle_expand",
                              text="", icon=expand_icon, emboss=False)
            # op.item_uuid = item.uuid

            # Ícone e nome da pasta
            row.prop(item, "name", text="", emboss=False, icon='FILE_FOLDER')

            # Controles de visibilidade
            visibility_icon = 'HIDE_OFF' if item.is_visible else 'HIDE_ON'
            row.prop(item, "is_visible", text="",
                     icon=visibility_icon, emboss=False)

        # Itens para grupos de vértices
        else:
            row.prop(item, "name", text="", emboss=False, icon='GROUP_VERTEX')

            # Link para o grupo real
            if item.group_name in context.object.vertex_groups:
                group = context.object.vertex_groups[item.group_name]
                visibility_icon = 'HIDE_OFF' if group.is_visible else 'HIDE_ON'
                row.prop(group, "name", text="",
                         icon=visibility_icon, emboss=False)
            else:
                row.label(text="Group Missing", icon='ERROR')


    def invoke(self, context, event):
        """Intercepta cliques do mouse para detectar Shift + Clique."""
        my_props = context.scene.my_props
        items = my_props.items

        if event.shift and my_props.last_clicked_index != -1:
            # Shift pressionado: seleciona todos no intervalo
            start = min(my_props.last_clicked_index, my_props.active_index)
            end = max(my_props.last_clicked_index, my_props.active_index)

            for i in range(start, end + 1):
                items[i].selected = True

        # Atualiza o índice do último clique
        my_props.last_clicked_index = my_props.active_index

        return {'FINISHED'}
        # # Verifica se o item está ativo
        # is_active = index == getattr(active_data, active_propname)

        # # Define o estilo de acordo com o estado ativo
        # if is_active:
        #     row.label(text="", icon='RADIOBUT_ON')  # Ícone de "selecionado"
        # else:
        #     # Ícone de "não selecionado"
        #     row.label(text="", icon='RADIOBUT_OFF')

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        hierarchy = get_hierarchy_dict(context.object.folder_hierarchy.expanded)
        
        filtered = [self.bitflag_filter_item] * len(items)
        ordered = []

        # Construir ordem hierárquica
        def add_children(parent_index):
            for idx, item in enumerate(items):
                if item.parent_uuid == parent_index:
                    ordered.append(idx)
                    if item.type == 'FOLDER' and item.is_expanded:
                        add_children(idx)

        # Adicionar itens raiz
        for idx, item in enumerate(items):
            if item.parent_uuid == -1:
                ordered.append(idx)
                if item.type == 'FOLDER' and item.is_expanded:
                    add_children(idx)

        # # Filtrar itens ocultos
        # for idx in reversed(range(len(items))):
        #     item = items[idx]
        #     if item.parent_uuid != -1:
        #         parent = items[item.parent_uuid]
        #         if not parent.is_expanded or parent.parent_uuid != -1 and not items[parent.parent_id].is_expanded:
        #             filtered[idx] &= ~self.bitflag_filter_item

        return filtered, ordered


def rebuild_hierarchy(obj):  # Função de volta ao escopo global
    """Recalcula a hierarquia para garantir a exibição correta."""
    for i, item in enumerate(obj.VCollection):
        if item.parent_uuid >= len(obj.VCollection):
            item.parent_uuid = -1  # Evita referências quebradas


class COLLECTION_OT_add_folder(bpy.types.Operator):
    """Adiciona uma nova pasta à hierarquia"""
    bl_idname = "vertex_collection.add_folder"
    bl_label = "Adicionar Pasta"

    def execute(self, context):
        obj = context.object
        active_idx = obj.VCollection_index
        
        new_item = obj.VCollection.add()
        new_item.uuid = generate_uuid()
        new_item.type = 'FOLDER'
        
        hierarchy = get_hierarchy_dict(obj)
        expandedHierarchy = get_hierarchy_dict(obj)
        
        # Verifica se é o primeiro item a ser criado
        # ou se não há item selecionado
        if len(obj.VCollection) == 1 or active_idx < 0:
            # Item raiz
            new_item.parent_uuid = "NoParent"  # Garante que não tem parent
            new_item.depth = 0
            new_item.name = generate_hierarchical_name(obj, None)
            new_item.is_expanded = False
            
            hierarchy[new_item.uuid] = {}
            set_hierarchy(obj, hierarchy)
            
            expandedHierarchy[new_item.uuid] = {}
            set_hierarchy(obj, expandedHierarchy)
        else:
            # Item filho
            parent_item = obj.VCollection[active_idx]
            if parent_item.type == 'FOLDER':
                new_item.parent_uuid = parent_item.uuid
                new_item.depth = parent_item.depth + 1
                new_item.name = generate_hierarchical_name(obj, parent_item)

                # Update hierarchy
                current_level = hierarchy
                parent_path = self.find_parent_path(hierarchy, parent_item.uuid)
                for uuid in parent_path if parent_path else []:
                    current_level = current_level[uuid]
                if isinstance(current_level.get(parent_item.uuid), dict):
                    current_level[parent_item.uuid][new_item.uuid] = {}
                else:
                    current_level[parent_item.uuid] = {new_item.uuid: {}}
            else:
                # Se o item selecionado não for uma pasta, cria como item raiz
                new_item.parent_uuid = ""
                new_item.depth = 0
                new_item.name = generate_hierarchical_name(obj, None)
                hierarchy[new_item.uuid] = {}

        # rebuild_hierarchy(obj)  # Chama rebuild_hierarchy após adicionar
        return {'FINISHED'}
    
    def find_parent_path(self, hierarchy, target_uuid, current_path=None):
        if current_path is None:
            current_path = []

        for uuid, children in hierarchy.items():
            if uuid == target_uuid:
                return current_path
            if isinstance(children, dict):
                new_path = self.find_parent_path(
                    children, target_uuid, current_path + [uuid])
                if new_path is not None:
                    return new_path

class COLLECTION_OT_add_group(bpy.types.Operator):
    """Adiciona grupo de vértices na hierarquia"""
    bl_idname = "vertex_collection.add_group"
    bl_label = "Add Vertex Group"

    def execute(self, context):
        obj = context.object
        new_item = obj.VCollection.add()

        # Criar grupo real
        vg = obj.vertex_groups.new(name=f"Group {len(obj.vertex_groups)+1}")

        # Configurar propriedades
        new_item.type = 'GROUP'
        new_item.name = vg.name
        new_item.group_name = vg.name

        # Definir hierarquia
        active_idx = obj.VCollection_index
        if active_idx >= 0 and active_idx < len(obj.VCollection):
            parent = obj.VCollection[active_idx]
            if parent.type == 'FOLDER':  # Adiciona sempre dentro da pasta selecionada
                new_item.parent_uuid = active_idx
                new_item.depth = parent.depth + 1

                # Expande a pasta pai automaticamente
                if not parent.is_expanded:
                    parent.is_expanded = True
                    rebuild_hierarchy(obj)  # Rebuild hierarchy to update UI

        obj.VCollection_index = len(obj.VCollection) - 1

        rebuild_hierarchy(obj)  # Chama rebuild_hierarchy após adicionar
        return {'FINISHED'}


class COLLECTION_OT_toggle_expand(bpy.types.Operator):
    """Alterna estado de expansão da pasta"""
    bl_idname = "vertex_collection.toggle_expand"
    bl_label = "Toggle Expand"
    item_index: bpy.props.IntProperty()

    def execute(self, context):
        item = context.object.VCollection[self.item_index]
        if item.type == 'FOLDER':
            item.is_expanded = not item.is_expanded
        # Chama rebuild_hierarchy após adicionar
        rebuild_hierarchy(context.object)
        return {'FINISHED'}


class COLLECTION_OT_remove_item(bpy.types.Operator):
    """Remove item da coleção e seus filhos, incluindo Vertex Groups reais."""
    bl_idname = "vertex_collection.remove_item"
    bl_label = "Remover Item"

    def execute(self, context):
        obj = context.object
        index = obj.VCollection_index

        if 0 <= index < len(obj.VCollection):
            item = obj.VCollection[index]

            def remove_children(parent_index):
                """Remove recursivamente todos os filhos."""
                to_remove = [idx for idx, child in enumerate(
                    obj.VCollection) if child.parent_uuid == parent_index]

                for child_idx in sorted(to_remove, reverse=True):
                    remove_children(child_idx)
                    child = obj.VCollection[child_idx]
                    self.remove_vertex_group(obj, child)  # Remove o grupo real
                    obj.VCollection.remove(child_idx)

            if item.type == 'FOLDER':
                remove_children(index)

            # Remove o grupo real (se for o caso)
            self.remove_vertex_group(obj, item)
            obj.VCollection.remove(index)

            if index > 0:
                obj.VCollection_index = index - 1
            else:
                obj.VCollection_index = 0

            rebuild_hierarchy(obj)

        rebuild_hierarchy(obj)  # Chama rebuild_hierarchy após adicionar
        return {'FINISHED'}

    def remove_vertex_group(self, obj, item):
        """Remove o Vertex Group real, se existir."""
        if item.type == 'GROUP' and item.group_name in obj.vertex_groups:
            group = obj.vertex_groups[item.group_name]
            obj.vertex_groups.remove(group)


class COLLECTION_OT_deselect_item(bpy.types.Operator):
    """Deseleciona o item ativo na lista."""
    bl_idname = "vertex_collection.deselect_item"
    bl_label = "Deselect"

    def execute(self, context):
        obj = context.object
        obj.VCollection_index = -1  # Define o índice para -1 para deselecionar
        return {'FINISHED'}


class DATA_PT_vertex_collections(bpy.types.Panel):
    """Painel principal para Vertex Collections"""
    bl_label = "Vertex Collections"
    bl_idname = "DATA_PT_vertex_collections"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if not obj or obj.type != 'MESH':
            return

        row = layout.row()
        row.template_list(
            "DATA_UL_vertex_collections",
            "",
            obj,
            "VCollection",
            obj,
            "VCollection_index",
            rows=8
        )

        col = row.column(align=True)
        col.operator("vertex_collection.add_folder", icon='NEWFOLDER', text="")
        col.operator("vertex_collection.add_group",
                     icon='GROUP_VERTEX', text="")
        col.operator("vertex_collection.remove_item", icon='REMOVE', text="")
        col.operator("vertex_collection.deselect_item",
                     icon='BLANK1', text="")  # Botão de deseleção


classes = (
    VertexCollectionItem,
    VertexCollectionHierarchy,
    DATA_UL_vertex_collections,
    COLLECTION_OT_add_folder,
    COLLECTION_OT_add_group,
    COLLECTION_OT_toggle_expand,
    COLLECTION_OT_remove_item,
    COLLECTION_OT_deselect_item,
    DATA_PT_vertex_collections,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_properties()


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Object, "VCollection"):
        del bpy.types.Object.VCollection
        del bpy.types.Object.VCollection_index


if __name__ == "__main__":
    register()
