import bpy
import re


arm = bpy.context.active_object

bones = arm.pose.bones

#bones =bpy.context.selected_pose_bones

# cycles through all pose bones
for bone in bones:
    #get bone name
    def_name = bone.name
    #find deform bones by prefix (using regex expression)
    match = re.match(r'^(DEF)(.*?)$', def_name)
    
    
    # if match found
    if match:
        #get pose bone by name
        def_bone = arm.pose.bones.get(def_name)
        #match group 1 is DEF. (from regex expression above)
        prefix = match.group(1)
        #match group 2 is everything else (from regex expression above)
        basename = match.group(2)
        #assemble target name by adding ORG. to the basename
        org_name = f'ORG{basename}'
        
        #check if target bone exists in the armature
        if arm.pose.bones.get(org_name) is not None:
            #add copy tranforms constraint if it does
            constraint = def_bone.constraints.new('COPY_TRANSFORMS')
            #set the contraint target to be the armature
            constraint.target = arm
            #set the constraint subtarget (Bone) to be the target bone
            constraint.subtarget = org_name
        
        else:
            # or print message to console if not
            print(f'{org_name} not found')
            
            
