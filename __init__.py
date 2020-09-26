
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

class State :
    effectManager=None
    effects={}
    lastTime=0

    def loadEffectsFromScene(self):
        self.effects={}
        for o in bpy.context.scene.objects:
            load=False
            if "_effekseer" in o:
                self.createEffect(o)

    def deleteEffect(self,o):
        uid=Utils.idOf(o)
        effect=  self.effects[uid] if uid in self.effects else None
        if effect!=None : 
            print("Delete",uid)
            effect.stop(self.effectManager)
            del   self.effects[uid]
            o["_effekseer"]=None
        return effect


    def createEffect(self,o):
        uid=Utils.idOf(o)
        effect=Effekt(uid)
        effect.setObjRef(o)
        self.effects[uid]=effect
        o["_effekseer"]=True
        print("Created effect for ",uid,":",effect)
        return effect

    def getEffect(self,o,create=False):
        uid=Utils.idOf(o)
        effect=  self.effects[uid] if uid in self.effects else None
        if effect==None and create: 
            print("No effect for ",uid)
            effect=self.createEffect(o)
        return effect




def onDraw(state):
    if state.effectManager==None: 
        EffekseerBackendCore_InitializeAsOpenGL()
        state.effectManager = EffekseerManagerCore()
        state.effectManager.Initialize(8000)        
        # state.effect = Effekt()
        # state.effect.setObjRef(bpy.context.scene.objects["Cube"])
        # state.effect.setPath("/home/riccardo/Desktop/jme-effekseerNative/src/test/resources/effekts/Pierre/Flame.efkefc")


    viewMatrix=gpu.matrix.get_model_view_matrix()
    state.effectManager.SetCameraMatrix(*Utils.getArrayFromMatrix(viewMatrix ,True)  )

    projectionMatrix=gpu.matrix.get_projection_matrix()
    state.effectManager.SetProjectionMatrix(*Utils.getArrayFromMatrix(projectionMatrix,True )  )

    frame=bpy.context.scene.frame_current
    time=   (float(frame )/ max(1.0, float(bpy.context.scene.render.fps)))
    time=time / (1.0/ 60.0)
    
    delta= 0.0 if state.lastTime==0.0 else time-state.lastTime
    state.lastTime=time

    for key,effect in state.effects.items():
            
        try:
            effect.update(
                effectManager=state.effectManager,
                wasFrameUpdated=delta!=0,
                t=time
            )
        except ReferenceError:
            print(key,"removed from scene. Delete associated effect")
            effect.stop(state.effectManager)
            del state.effects[key]
            break

    # if delta<0:
    # state.effect.step(state.effectManager,time)
    # else:

    if delta>0:
        state.effectManager.Update(delta)
    else:
        state.effectManager.BeginUpdate()
        for effect in state.effects.values():
            if effect.getHandle()!=None:
                state.effectManager.UpdateHandleToMoveToFrame(effect.getHandle(),time)
        state.effectManager.EndUpdate()
        

    state.effectManager.DrawBack()
    state.effectManager.DrawFront()


drawHandler=None
def register():
    print("Load Effekseer renderer")
    global drawHandler
    state =State()
    drawHandler=bpy.types.SpaceView3D.draw_handler_add(onDraw,(state,),"WINDOW","POST_VIEW")
    EffekseerUI.register(state)

def unregister():
    global drawHandler
    if drawHandler!=None:
        drawHandler=None
        bpy.types.SpaceView3D.draw_handler_remove(drawHandler,"WINDOW")


if __name__ == '__main__':
    register()
