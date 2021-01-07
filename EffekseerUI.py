
from bpy.types import Menu, Panel, UIList,UILayout,Operator
import bpy
from bpy_extras.io_utils import ImportHelper 
from bpy.types import Operator
from bpy.props import StringProperty
import os
from . import Utils


STATE=None

DYNAMIC_PROP_CLASSES={}
def getDynamicInputs(o,effect):
    global DYNAMIC_PROP_CLASSES
    uid=Utils.idOf(o)
    inputs=effect.getDynamicInputs()
    propKey="effekseer_dyns_inputs"+str(len(inputs))
    print("Use property key",propKey)

    instance=getattr(o,propKey,None)
    if instance:
        return instance

    claz=DYNAMIC_PROP_CLASSES[propKey] if propKey in DYNAMIC_PROP_CLASSES else None
    if claz:
        bpy.utils.unregister_class(claz)

    inputsV={}

    for i in range(0,len(inputs)):
        key="Input"+str(i)
        inputsV[key]=bpy.props.FloatProperty(name=key, default=inputs[i],update=_onUpdate)

    claz = type("Dynamic Inputs", (bpy.types.PropertyGroup,), inputsV)
    DYNAMIC_PROP_CLASSES[propKey]=claz
    bpy.utils.register_class(claz )

    setattr(bpy.types.Object,  propKey,bpy.props.PointerProperty(type=claz))
    return getattr(o, propKey)
    






def onUpdate(self,context,target=None):
    if not target: target= bpy.context.active_object
    effect=STATE.getEffect(target,True)
    if self and getattr(self, "filePath", None):
        filePath=self.filePath
        extension = os.path.splitext(filePath)[1]
        if extension!=".efkefc":
            bpy.context.window_manager.popup_menu(lambda self,context:        self.layout.label(text="Can't load "+filePath+" with extension "+extension+". Only efkefc files are supported")    , title = "Can't load effect", icon = "ERROR")
            self.filePath=""
            return
        if self.relPaths and  bpy.data.is_saved:
            pp=bpy.path.relpath(self.filePath)
        else:
            pp=self.filePath
        print("Path:",self.filePath,"relpath",pp)
        effect.setPath(pp)
    if self and getattr(self, "scale", None):
        effect.setScale(self.scale)
    if self and getattr(self, "ignoreRot", None)!=None:
        effect.setIgnoreRotation(self.ignoreRot)
    if self and getattr(self, "enabled", None)!=None:
        effect.setEnabled(STATE.effectManager,self.enabled)
    if self:
        i=0
        while True:
            v=getattr(self, "Input"+str(i), None)
            if v!=None:
                effect.setDynamicInput(i,v)
                i+=1
            else: break
    getDynamicInputs(target,effect)


def _onUpdate(self,context):
    onUpdate(self,context)

class EFFEKSEER_addDynInput(Operator):
    bl_idname = "effekseer.add_dyn_input"
    bl_label = "Add dynamic input"

    def execute(self, context):
        target= bpy.context.active_object
        effect=STATE.getEffect(target,False)
        if effect:
            effect.setDynamicInput(len(effect.getDynamicInputs()),0)
            getDynamicInputs(target,effect)
        return {"FINISHED"}
        

class EFFEKSEER_removeDynInput(Operator):
    bl_idname = "effekseer.remove_dyn_input"
    bl_label = "Remove dynamic input"

    def execute(self, context):
        target= bpy.context.active_object
        effect=STATE.getEffect(target,False)
        if effect:
            effect.unsetDynamicInput(len(effect.getDynamicInputs())-1)
            getDynamicInputs(target,effect)
        return {"FINISHED"}


class EFFEKSEER_deleteEffect(Operator):
    bl_idname = "effekseer.delete_effect"
    bl_label = "Remove effect"

    def execute(self, context):
        target= bpy.context.active_object
        target.effekseer_settings.filePath=""
        STATE.deleteEffect(target)
        return {"FINISHED"}


        

class EFFEKSEER_settings(bpy.types.PropertyGroup):

    filePath: bpy.props.StringProperty(update=_onUpdate,name="Path",
                                        description="Effect Path",
                                        maxlen=1024,
                                        subtype="FILE_PATH")
    scale:bpy.props.FloatProperty(update=_onUpdate,name="Scale",description="Effect Scale",default=1.0)
    ignoreRot:bpy.props.BoolProperty(update=_onUpdate,name="Ignore rotation",description="Ignore object rotation",default=False)
    enabled:bpy.props.BoolProperty(update=_onUpdate,name="Enabled",description="Set effect enabled",default=True)
    relPaths:bpy.props.BoolProperty(update=_onUpdate,name="Use relative paths",description="Use relative paths",default=False)


class EFFEKSEER_PT_particle_panel(Panel):
    bl_label = "Effekseer Emitter"
    bl_idname = "EFFEKSEER_PT_particle_panel"
    bl_context = "object"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    COMPAT_ENGINES = {'BLENDER_EEVEE'}

    def draw(self, context):
        target= bpy.context.active_object
        settings = target.effekseer_settings

        effect=STATE.getEffect(target,settings.filePath!="")
        self.layout.use_property_split = True

        layout = self.layout

        row = layout.row()
        row.prop(settings, "relPaths")
        row.enabled=bpy.data.is_saved
    
        row = layout.row()
        row.label(text="Effect")
        split = row.split(factor=0.8)
        c= split.column()
        path=c.prop(settings, "filePath")
        enabled= settings.filePath!=""
        c= split.column()
        c.operator("effekseer.delete_effect",text="X")
        c.enabled=enabled

        row = layout.row()
        row.prop(settings, "scale")
        row.enabled=enabled

        row = layout.row()
        row.prop(settings, "ignoreRot")
        row.enabled=enabled

        row = layout.row()
        row.prop(settings, "enabled")
        row.enabled=enabled

        row = layout.row()
        row.label(text="Dynamic Inputs")
        row.enabled=enabled
        if effect:
            inputs=effect.getDynamicInputs()
            if len(inputs)>0:
                dynIn=getDynamicInputs(target,effect)
                if dynIn:
                    for i in range(0,len(inputs)):
                        key="Input"+str(i)
                        row = layout.row()
                        row.enabled=enabled
                        row.prop(dynIn,key)
                    row = layout.row()
                    row.enabled=enabled
            split = row.split(factor=0.5)

            c= split.column()
            c.operator("effekseer.add_dyn_input",text="+")
            c= split.column()
            c.operator("effekseer.remove_dyn_input",text="-")
            c.enabled=(len(inputs)>0)




def register(state):
    print("Register UI")
    global STATE
    STATE=state
    bpy.utils.register_class(EFFEKSEER_settings)
    bpy.utils.register_class(EFFEKSEER_addDynInput)
    bpy.utils.register_class(EFFEKSEER_removeDynInput)
    bpy.utils.register_class(EFFEKSEER_deleteEffect)
    bpy.types.Object.effekseer_settings = bpy.props.PointerProperty(type=EFFEKSEER_settings)
    bpy.utils.register_class(EFFEKSEER_PT_particle_panel)

def unregister(state):
    print("Register UI")
    global STATE
    STATE=state
    bpy.utils.unregister_class(EFFEKSEER_settings)
    bpy.utils.unregister_class(EFFEKSEER_addDynInput)
    bpy.utils.unregister_class(EFFEKSEER_removeDynInput)
    bpy.utils.unregister_class(EFFEKSEER_deleteEffect)
    bpy.types.Object.effekseer_settings = bpy.props.PointerProperty(type=EFFEKSEER_settings)
    bpy.utils.unregister_class(EFFEKSEER_PT_particle_panel)
