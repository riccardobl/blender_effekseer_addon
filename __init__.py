
bl_info = {
        "name": "Effekseer For Blender",
        "description": "Render effekseer on blender",
        "author": "Riccardo Balbo",
        "version": (1, 0),
        "blender": (2, 80, 0),
        "category" : "Render",
        "location" : "",
        "warning" : "",
}

import ctypes
import os
import bpy
import gpu
import bgl
import pathlib
from .EffekseerCore import *;
from .Effekt import *
from . import Utils
from . import EffekseerUI
import mathutils
from bpy.app.handlers import persistent
class State :
    effectManager=None
    effects={}
    lastTime=0

    def loadEffectsFromScene(self):
        self.effects={}
        for o in bpy.context.scene.objects:
            if "_effekseer" in o:
                print("Load effect for",o)
                ef=self.createEffect(o)
                EffekseerUI.onUpdate(None,None,o)

    def deleteEffect(self,o):
        uid=Utils.idOf(o)
        effect=  self.effects[uid] if uid in self.effects else None
        if effect!=None : 
            effect.stop(self.effectManager)
        return effect

    def clear(self):
        for e in self.effects.values():
            e.stop(self.effectManager)
        self.lastTime=0
        self.effects={}


    def createEffect(self,o):
        uid=Utils.idOf(o)
        effect=Effekt(uid)
        effect.setObjRef(o)
        self.effects[uid]=effect
        if not "_effekseer" in o: o["_effekseer"]=True
        print("Created effect for ",uid,":",effect)
        return effect

    def getEffect(self,o,create=False):
        uid=Utils.idOf(o)
        effect=  self.effects[uid] if uid in self.effects else None
        if effect==None and create: 
            effect=self.createEffect(o)
        return effect


def onDestroy(state):
    state.clear()
    if state.effectManager!=None:
        state.effectManager=None
        # state.effectManager.delete()
        EffekseerBackendCore_Terminate()

def onDraw(state):
    if state.effectManager==None: 
        EffekseerBackendCore_InitializeAsOpenGL()
        state.effectManager = EffekseerManagerCore()
        state.effectManager.Initialize(8000)        


    viewMatrix=gpu.matrix.get_model_view_matrix()
    viewMatrix=viewMatrix @ mathutils.Matrix(
            [
                [1 ,0, 0, 0], 
                [0, 0 ,-1 ,0], 
                [0, 1, 0, 0], 
                [0, 0, 0, 1]
            ]
        )
    state.effectManager.SetCameraMatrix(*Utils.getArrayFromMatrix(viewMatrix ,True)  )

    projectionMatrix=gpu.matrix.get_projection_matrix()
    state.effectManager.SetProjectionMatrix(*Utils.getArrayFromMatrix(projectionMatrix,True )  )

    frame=bpy.context.scene.frame_current
    time=   (float(frame )/ max(1.0, float(bpy.context.scene.render.fps)))
    time=time / (1.0/ 60.0)
    
    delta= 0.0 if state.lastTime==0.0 else time-state.lastTime
    state.lastTime=time

    renderMode=False
    for key,effect in state.effects.items():
        renderMode=effect.prepareRender(state.effectManager,time,delta,renderMode)

    Effekt.beginUpdate(state.effectManager,time,delta,renderMode)
    
    for key,effect in state.effects.items():
        markForDelete=False
        noObj=False
        try:
            markForDelete=effect.update(
                effectManager=state.effectManager,
                t=time,
                delta=delta,
                renderMode=renderMode
            )            
        except ReferenceError:
            print(key,"removed from scene. Delete associated effect")
            markForDelete=True
            noObj=True

        if markForDelete:
            if not noObj: effect.getObjRef()["_effekseer"]=None
            effect.stop(state.effectManager)
            del state.effects[key]            
            print("Delete",key)
            break
    
    Effekt.endUpdate(state.effectManager,time,delta,renderMode)


    ov=bgl.glIsEnabled(bgl.GL_FRAMEBUFFER_SRGB)
    if ov:bgl.glDisable(bgl.GL_FRAMEBUFFER_SRGB); 
    state.effectManager.DrawBack()
    state.effectManager.DrawFront()
    if ov: bgl.glEnable(bgl.GL_FRAMEBUFFER_SRGB); 


drawHandler=None
state=None

@persistent
def onLoad(dummy):
    print("Load effects from scene")
    onDestroy(state)
    bpy.app.handlers.depsgraph_update_post.remove(onLoad)
    state.loadEffectsFromScene()

@persistent
def loadHandler(dummy):
    print("Load Handler:", bpy.data.filepath)
    bpy.app.handlers.depsgraph_update_post.append(onLoad)



def register():
    print("Load Effekseer renderer")
    global drawHandler
    global state
    bpy.app.handlers.load_post.append(loadHandler)
    state =State()
    drawHandler=bpy.types.SpaceView3D.draw_handler_add(onDraw,(state,),"WINDOW","POST_VIEW")
    EffekseerUI.register(state)

def unregister():
    global drawHandler
    EffekseerUI.unregister(state)
    if drawHandler!=None:
        bpy.types.SpaceView3D.draw_handler_remove(drawHandler,"WINDOW")
        drawHandler=None
    bpy.app.handlers.depsgraph_update_post.remove(onLoad)


if __name__ == '__main__':
    register()
