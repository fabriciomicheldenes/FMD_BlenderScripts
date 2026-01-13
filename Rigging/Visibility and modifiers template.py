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
      
