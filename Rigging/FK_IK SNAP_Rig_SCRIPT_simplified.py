
import bpy

##library to be added##

from mathutils import Euler, Matrix, Vector, Quaternion

######################### Snap functions ############################

# returns final world matrix accounting for offset in rest pose
def get_matrix(armature, source_bone, target_bone):
    # rest post matrices
    source_bone_rest_matrix = source_bone.bone.matrix_local
    target_bone_rest_matrix = target_bone.bone.matrix_local

    # rest pose offset matrix
    offset_matrix = source_bone_rest_matrix.inverted() @ target_bone_rest_matrix

    # world_space_matrices
    source_world_matrix = source_bone.matrix

    #world space matrix
    matrix_final =  source_world_matrix @ offset_matrix
    
    return matrix_final

######################### Snap Operators ############################

### ARMS ###
### Snapping IK to FK ####
### We create MCH bones that are children of the FK chain to snap our IK controllers to###

class MY_RIG_NAME_OT_ik_fk_arm(bpy.types.Operator):
    bl_idname = "my_rig_name.ik_fk_arm"
    bl_label = ""
    bl_description = "Snap IK > FK"
    bl_options = {'UNDO', 'INTERNAL'}
    
    side: bpy.props.StringProperty(name="'L' or 'R'")

    @classmethod
    def poll(self, context):
        try:
            return (context.active_object.data.get("rig_id") == rig_id)
        except (AttributeError, KeyError, TypeError):
            return False
    
    def execute(self, context):
        side = self.side
        armature = bpy.context.active_object
        pose_bones = armature.pose.bones
        #name of the custom properties bone
        properties = pose_bones['PROPERTIES']
        
        # FK BONES TO SNAP TO
        fk_hand = pose_bones[f'MCH_FK_IK_HAND.{side}']
        fk_pole = pose_bones[f'MCH_FK_IK_POLE.{side}']
                
        # IK BONES
        ik_hand = pose_bones[f'HAND_IK.{side}']
        ik_pole = pose_bones[f'ARM_POLE_IK.{side}']
                
        select_set = (ik_hand, ik_pole, properties) 
        
        hand_matrix = get_matrix(armature, fk_hand, ik_hand )
        pole_matrix = get_matrix(armature, fk_pole, ik_pole )
        
        ik_hand.matrix = hand_matrix
        bpy.context.view_layer.update()        
        ik_pole.matrix = pole_matrix
        bpy.context.view_layer.update()
        
        # switch_mode   
        properties[f'ARM_IK_FK.{side}'] = 0        
        
        bpy.ops.pose.select_all(action='DESELECT')
        
        for pbone in select_set:
            armature.data.bones.active = pbone.bone

            if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
                try:
                    bpy.ops.anim.keyframe_insert_menu(type='Available')
                except RuntimeError:
                    self.report({'WARNING'}, f'{pbone.name} has no active keyframes')
                    pass        
        
        return {'FINISHED'}      


### ARMS ###
### Snapping FK to IK ####
### We use the MCH bones of the IK chain to snap the FK chain to ###

class MY_RIG_NAME_OT_fk_ik_arm(bpy.types.Operator):
    bl_idname = "my_rig_name.fk_ik_arm"
    bl_label = ""
    bl_description = "Snap IK > FK"
    bl_options = {'UNDO', 'INTERNAL'}
    
    side: bpy.props.StringProperty(name="'L' or 'R'")

    @classmethod
    def poll(self, context):
        try:
            return (context.active_object.data.get("rig_id") == rig_id)
        except (AttributeError, KeyError, TypeError):
            return False
    
    def execute(self, context):
        side = self.side
        armature = bpy.context.active_object
        pose_bones = armature.pose.bones
        #name of the custom properties bone
        properties = pose_bones['PROPERTIES']
        
        # FK BONES
        fk_hand = pose_bones[f'HAND_FK.{side}']
        fk_forearm = pose_bones[f'FOREARM_FK.{side}']
        fk_arm = pose_bones[f'ARM_FK.{side}']
                
        # IK BONES TO SNAP TO
        ik_hand = pose_bones[f'MCH_IK_HAND.{side}']
        ik_forearm = pose_bones[f'MCH_IK_FOREARM.{side}']
        ik_arm = pose_bones[f'MCH_IK_ARM.{side}']
                
        select_set = (fk_hand, fk_forearm, fk_arm, properties) 
        
        hand_matrix = get_matrix(armature, ik_hand, fk_hand )
        forearm_matrix = get_matrix(armature, ik_forearm, fk_forearm )
        arm_matrix = get_matrix(armature, ik_arm, fk_arm )
        
### order may matrer ##
        fk_arm.matrix = arm_matrix
        bpy.context.view_layer.update()
        fk_forearm.matrix = forearm_matrix
        bpy.context.view_layer.update()
        fk_hand.matrix = hand_matrix
        bpy.context.view_layer.update()        
                
        
        # switch_mode   
        properties[f'ARM_IK_FK.{side}'] = 1        
        
        bpy.ops.pose.select_all(action='DESELECT')
        
        for pbone in select_set:
            armature.data.bones.active = pbone.bone

            if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
                try:
                    bpy.ops.anim.keyframe_insert_menu(type='Available')
                except RuntimeError:
                    self.report({'WARNING'}, f'{pbone.name} has no active keyframes')
                    pass        
        
        return {'FINISHED'}      

### LEGS ###
### Snapping IK to FK ####
### We create MCH bones that are children of the FK chain to snap our IK controllers to###

class MY_RIG_NAME_OT_ik_fk_leg(bpy.types.Operator):
    bl_idname = "my_rig_name.ik_fk_leg"
    bl_label = ""
    bl_description = "Snap IK > FK"
    bl_options = {'UNDO', 'INTERNAL'}
    
    side: bpy.props.StringProperty(name="'L' or 'R'")

    @classmethod
    def poll(self, context):
        try:
            return (context.active_object.data.get("rig_id") == rig_id)
        except (AttributeError, KeyError, TypeError):
            return False
    
    def execute(self, context):
        side = self.side
        armature = bpy.context.active_object
        pose_bones = armature.pose.bones
        #name of the custom properties bone
        properties = pose_bones['PROPERTIES']
        
        # FK BONES TO SNAP TO
        fk_foot = pose_bones[f'MCH_FK_IK_FOOT.{side}']
        fk_pole = pose_bones[f'MCH_FK_IK_POLE.{side}']
                
        # IK BONES
        ik_foot = pose_bones[f'FOOT_IK.{side}']
        ik_pole = pose_bones[f'LEG_POLE_IK.{side}']
                
        select_set = (ik_foot, ik_pole, properties) 
        
        foot_matrix = get_matrix(armature, fk_foot, ik_foot )
        pole_matrix = get_matrix(armature, fk_pole, ik_pole )
        
        ik_foot.matrix = foot_matrix
        bpy.context.view_layer.update()        
        ik_pole.matrix = pole_matrix
        bpy.context.view_layer.update()
        
        # switch_mode   
        properties[f'LEG_IK_FK.{side}'] = 0        
        
        bpy.ops.pose.select_all(action='DESELECT')
        
        for pbone in select_set:
            armature.data.bones.active = pbone.bone

            if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
                try:
                    bpy.ops.anim.keyframe_insert_menu(type='Available')
                except RuntimeError:
                    self.report({'WARNING'}, f'{pbone.name} has no active keyframes')
                    pass        
        
        return {'FINISHED'}      


### LEGS ###
### Snapping FK to IK ####
### We use the MCH bones of the IK chain to snap the FK chain to ###

class MY_RIG_NAME_OT_fk_ik_leg(bpy.types.Operator):
    bl_idname = "my_rig_name.fk_ik_leg"
    bl_label = ""
    bl_description = "Snap IK > FK"
    bl_options = {'UNDO', 'INTERNAL'}
    
    side: bpy.props.StringProperty(name="'L' or 'R'")

    @classmethod
    def poll(self, context):
        try:
            return (context.active_object.data.get("rig_id") == rig_id)
        except (AttributeError, KeyError, TypeError):
            return False
    
    def execute(self, context):
        side = self.side
        armature = bpy.context.active_object
        pose_bones = armature.pose.bones
        #name of the custom properties bone
        properties = pose_bones['PROPERTIES']
        
        # FK BONES
        fk_foot = pose_bones[f'FOOT_FK.{side}']
        fk_shin = pose_bones[f'SHIN_FK.{side}']
        fk_thigh = pose_bones[f'THIGH_FK.{side}']
                
        # IK BONES TO SNAP TO
        ik_foot = pose_bones[f'MCH_IK_FOOT.{side}']
        ik_shin = pose_bones[f'MCH_IK_SHIN.{side}']
        ik_thigh = pose_bones[f'MCH_IK_THIGH.{side}']
                
        select_set = (fk_foot, fk_shin, fk_thigh, properties) 
        
        foot_matrix = get_matrix(armature, ik_foot, fk_foot )
        shin_matrix = get_matrix(armature, ik_shin, fk_shin )
        thigh_matrix = get_matrix(armature, ik_thigh, fk_thigh )
        
### order may matrer ##
        fk_thigh.matrix = thigh_matrix
        bpy.context.view_layer.update()
        fk_shin.matrix = shin_matrix
        bpy.context.view_layer.update()
        fk_foot.matrix = foot_matrix
        bpy.context.view_layer.update()        
                
        
        # switch_mode   
        properties[f'LEG_IK_FK.{side}'] = 1        
        
        bpy.ops.pose.select_all(action='DESELECT')
        
        for pbone in select_set:
            armature.data.bones.active = pbone.bone

            if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
                try:
                    bpy.ops.anim.keyframe_insert_menu(type='Available')
                except RuntimeError:
                    self.report({'WARNING'}, f'{pbone.name} has no active keyframes')
                    pass        
        
        return {'FINISHED'}      



##################################################################################  

### We display our snapping tools in a panel ###

class MY_RIG_NAME_PT_snap_panel(bpy.types.Panel):
    bl_category = 'Item'
    bl_label = "Snap Utilities"
    bl_idname = "MY_RIG_NAME_PT_snap_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        try:
            return (context.active_object.data.get("rig_id") == rig_id)
        except (AttributeError, KeyError, TypeError):
            return False
        
    def draw(self, context):
        layout = self.layout
        #box = layout.box()
        col = layout.column(align=True)
        row = col.row()
        row.operator("my_rig_name.ik_fk_arm", emboss=True, text="Arm L IK > FK", icon='SNAP_ON').side = 'L'
        row.operator("my_rig_name.ik_fk_arm", emboss=True, text="Arm R IK > FK", icon='SNAP_ON').side = 'R'
        
        row = col.row()
        row.operator("my_rig_name.fk_ik_arm", emboss=True, text="Arm L FK > IK", icon='SNAP_ON').side = 'L'
        row.operator("my_rig_name.fk_ik_arm", emboss=True, text="Arm R FK > IK", icon='SNAP_ON').side = 'R'
        
        col = layout.column(align=True)
        row = col.row()
        row.operator("my_rig_name.ik_fk_leg", emboss=True, text="Leg L IK > FK", icon='SNAP_ON').side = 'L'
        row.operator("my_rig_name.ik_fk_leg", emboss=True, text="Leg R IK > FK", icon='SNAP_ON').side = 'R'
        
        row = col.row()
        row.operator("my_rig_name.fk_ik_leg", emboss=True, text="Leg L FK > IK", icon='SNAP_ON').side = 'L'
        row.operator("my_rig_name.fk_ik_leg", emboss=True, text="Leg R FK > IK", icon='SNAP_ON').side = 'R'
                                            
##################################################################################                                            

### Operators and panels must be registered #######                                            

#THE ORDER HERE DEFINES THE ORDER IN THE PANEL
classes = ( MyRigName_PT_snap_panel,
            MyRigName_OT_ik_fk_arm,
            MyRigName_OT_fk_ik_arm,
            MyRigName_OT_ik_fk_leg,
            MyRigName_OT_fk_ik_leg,)
register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
	register()