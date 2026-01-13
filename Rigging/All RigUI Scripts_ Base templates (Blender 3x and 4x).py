

import bpy

###Set a rig ID in your armature custom properties using a string
rig_id = "MyRigId"

######################################################################################

### Displaying bone collections (Blender 4.0 and above)
class MyRig_PT_rigui(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'
    bl_label = "Rig UI"
    bl_idname = "MyRig_PT_rigui"


### Check if the selected rig has the corresponding RigID
    @classmethod
    def poll(self, context):
        try:
            return (context.active_object.data.get("rig_id") == rig_id)
        except (AttributeError, KeyError, TypeError):
            return False


    def draw(self, context):
        layout = self.layout
        col = layout.column()
        ### get the bone collection from our Armature. "Armature" is the name of our armature
        collection = bpy.data.armatures["Armature"].collections

        ### We can create rows exposing the visibility of our bone collection and give them a name 
        row = col.row(align = True)  
        row.prop(collection["ROOT"], 'is_visible', toggle=True, text='ROOT')
                
        row = col.row(align = True)  
        row.prop(collection["LEG.L"], 'is_visible', toggle=True, text='LEG.L')
        row.prop(collection["LEG.R"], 'is_visible', toggle=True, text='LEG.R')
        
######################################################################################

### Displaying bone layers (Blender 3.6 and previous)
class MyRig_PT_rigui(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'
    bl_label = "Rig UI"
    bl_idname = "MyRig_PT_rigui"


### Check if the selected rig has the corresponding RigID
    @classmethod
    def poll(self, context):
        try:
            return (context.active_object.data.get("rig_id") == rig_id)
        except (AttributeError, KeyError, TypeError):
            return False


    def draw(self, context):
        layout = self.layout
        col = layout.column()


        ### displaying the bone layers using their index and give them a name
        row = col.row(align=True)
        row.prop(context.active_object.data,'layers', index=22, toggle=True, text='ARM-FK.L')
        row.prop(context.active_object.data,'layers', index=23, toggle=True, text='ARM-IK.L')


######################################################################################

###Custom properties panel 
### THIS IS ONLY THE PARENT PANEL FOR ALL THE SUB PANELS
class MyRig_PT_customprops(bpy.types.Panel):
    bl_category = 'Item'
    bl_label = "Rig Properties"
    bl_idname = "MyRig_PT_customprops"
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

# EACH SUB PANEL IS A CLASS
class MyRig_PT_arm_props(bpy.types.Panel):
    bl_label = "Arm Properties" 
    bl_idname = "MyRig_PT_arm_props"
    bl_space_type = 'VIEW_3D'
    bl_parent_id = "MyRig_PT_customprops" # this is the same for all it points to the main panel name
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'} # you may not want this? delete if not
    
    def draw(self, context):
        
        # get armature and "PROPERTIES" bone 
        arm = context.active_object
        bone = arm.pose.bones["PROPERTIES"]
        
        # basic layout setup
        layout = self.layout
        # just in we case want to change the split makes make a variable
        split_size = 0.7
        
        # then we start making rows, the first one is in a box      
        box = layout.box()
        col = box.column(align=True)
        row = col.row()              
        split = row.split(align=True, factor=split_size)
        row = split.row(align=True)        
        # this is just the label you could call it anything
        row.label(text='ARM FK-IK.L', translate=False)
        row = split.row(align=True)
        # this is the property > format is important
        row.prop(bone, '["ARM_IK_FK.L"]', text = "", slider=True)
        
        # copy paste repeat... test as you go, the second one is in the same box
        row = col.row() 
        split = row.split(align=True, factor=split_size)
        row = split.row(align=True)
        row.label(text='ARM FK-IK.R', translate=False)
        row = split.row(align=True)
        row.prop(bone, '["ARM_IK_FK.R"]', text = "", slider=True)
        


######################################################################################

#Exposing modifiers, mostly used for mask modifiers in this course.
class MyRig_PT_vis_props(bpy.types.Panel):
    bl_label = "Visibility Properties" 
    bl_idname = "MyRig_PT_vis_props"
    bl_space_type = 'VIEW_3D'
    bl_parent_id = "MyRig_PT_customprops"
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        
        # object list (if you change object names it you will have to change these too) We can create as many variable as we want to source asmany objects as we want
        my_object =  bpy.data.objects['my_object_name']
               
        # character modifiers use modifier names (if you change modifier names it you will have to change these too). Here we have an edxample with mask modifiers.
        # creating a variable to source the modifier (name_of_the_variable = my_object.modifiers["exact_modifier_name"])
        mask_arms = my_object.modifiers["MASK-ARMS"]
        mask_legs = my_object.modifiers["MASK-LEGS"]
        
        
        # start panel layout
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False 
        
        # character modifiers
        # if I didn't break it down above the code would be: (kinda messy)
        # row.prop(bpy.data.objects['my_object'].modifiers["MASK-TORSO"], 'show_viewport', text="", toggle = True, icon='HIDE_ON', emboss=False)  
        # here we use Blender's eye/hide icon
        box = layout.box()
        col = box.column(align=True)
        row = col.row() 
        row.label(text='Arms', translate=False)   
        row.prop(mask_arms, 'show_viewport', text="", icon='HIDE_ON', invert_checkbox=True, emboss=False)
        
        row = col.row(align = True)  
        row.label(text='Legs', translate=False)             
        row.prop(mask_legs, 'show_viewport', text="", icon='HIDE_ON', invert_checkbox=True, emboss=False)        
        
######################################################################################
  

### To use and display classes, we need to register them. Add your panerls and operators to the list below. This is the end of our script
                                            
classes = (mypannel_1,
           mypannel_2)

register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()