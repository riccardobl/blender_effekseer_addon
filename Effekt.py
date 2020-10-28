from .EffekseerCore import *;
from . import Utils
import bpy
import uuid
import mathutils
class Effekt:

    def __init__(self,uid):
        self.path=None
        self.objRef=None
        self.initialized=False
        self.effect=None
        self.effectHandle=None
        self.uid=uid
        self.reinit=False
        self.scale=1.0
        self.inputs=[]
        self.ignoreRotation=False
        self.duration=0
        self.loop=True
        self.enabled=True
        self.ended=False
        self.isNew=True
        self.lastTransformMatrix=None
        self.markOfDeath=False

    def setDynamicInput(self,i,v,quiet=False):
        while i>=len(self.inputs):
            self.inputs.append(0)
        self.inputs[i]=v
        if not quiet: self.serialize()

    def unsetDynamicInput(self,i):
        self.inputs.pop(i)

    def getDynamicInputs(self):
        return self.inputs


    def setScale(self,v):
        self.scale=v
        self.serialize()

    def getScale(self):
        return self.scale
      
    def setObjRef(self,objRef):
        self.objRef=objRef
        if objRef!=None:self.deserialize(objRef)

    def setPath(self,path):
        if path!=self.path:
            self.path=path
            self.serialize()
            self.reinit=True

    def getPath(self):
        return self.path

    def getObjRef(self):
        return self.objRef


    def setLoop(self,v):
        self.loop=v

    def isLoop(self):
        return self.loop


    def setEnabled(self,effectManager,v):
        self.enabled=v
        if self.getHandle():effectManager.SetShown(self.getHandle(),v)
        self.serialize()
    
    def isEnabled(self):
        return self.enabled
        
    def stop(self,effectManager):
        if not self.markOfDeath:
            # if self.effect!=None: self.effect.delete()
            if self.effectHandle!=None:
                effectManager.SetShown(self.getHandle(),False)
                effectManager.Stop(self.effectHandle)
                self.markOfDeath=True

    def prepareRender(self,effectManager,time,delta,currentMode):
        mode=True
        if delta<=0 or self.isNew: 
            mode=True

        return currentMode or mode

    def update(self,effectManager,t,delta,renderMode,visible):
        self.initFromRenderThread(effectManager)
        if not self.initialized or self.effect==None: 
            return

        if self.markOfDeath: 
            return True

        visible=visible and not self.getObjRef().hide_get()
        if visible:
            exists=self.effectHandle!=None and effectManager.Exists(self.effectHandle)
            if not(exists) :
                if delta!=0 or self.isNew:
                    self.effectHandle=effectManager.Play(self.effect)
                    self.isNew=True
                else: 
                    return

            transformMatrix=self.objRef.matrix_world

            loc, rot, scale = transformMatrix.decompose()
            scale=Utils.swizzleScale(scale)*self.getScale()
            loc=Utils.swizzleLoc(loc)            

            if  self.ignoreRotation:   rot=mathutils.Quaternion()
            else:  rot=Utils.swizzleRot(rot)

            transformMatrix = Utils.toMatrix(loc,rot,scale)

            updatedTransform=self.lastTransformMatrix==None or transformMatrix!=self.lastTransformMatrix
            self.lastTransformMatrix=transformMatrix

            if self.isNew or updatedTransform or delta!=0:
                effectManager.SetEffectTransformBaseMatrix(self.effectHandle,*Utils.getArrayFromMatrix(transformMatrix,True,3))

                self.ended=not( t<self.duration or self.isLoop())
                if not self.ended:                     
                    if renderMode : 
                        # Step update
                        tt=t%self.duration       
                        if delta==0:  # HacK: Force update even if the effect didn't move(?)
                            effectManager.UpdateHandleToMoveToFrame(self.getHandle(),tt-0.01)
                            effectManager.UpdateHandleToMoveToFrame(self.getHandle(),tt)
                        else:                                
                            effectManager.UpdateHandleToMoveToFrame(self.getHandle(),tt)
                    else:
                        # Normal update
                        pass
            self.isNew=False

        if self.effectHandle!=None:
            effectManager.SetShown(self.getHandle(),self.enabled and visible and not self.ended)
   
        return False        
            

    @staticmethod
    def beginUpdate(effectManager,time,delta,renderMode):
        if  renderMode: effectManager.BeginUpdate()

    @staticmethod
    def endUpdate(effectManager,time,delta,renderMode):
        if renderMode: effectManager.EndUpdate()
        # effectManager.Update(delta)


    def getHandle(self):
        return self.effectHandle


    def deserialize(self,objRef):
        self.objRef=objRef
        self.initialized=False
        if "_effekseer_path" in  self.objRef:
            self.path=  self.objRef["_effekseer_path"]
        if   "_effekseer_scale" in self.objRef:
            self.scale= float( self.objRef["_effekseer_scale"])
        if "_effekseer_ignorerot" in self.objRef:
            self.ignoreRotation=bool(self.objRef["_effekseer_ignorerot"])
        if "_effekseer_enabled" in self.objRef:
            self.enabled=bool(self.objRef["_effekseer_enabled"])

        i=0
        while True:
            k= "_effekseer_input"+str(i) 
            if  k in self.objRef:
                self.setDynamicInput(i, float( self.objRef[k]),True)
                i+=1
            else:
                break        

    def serialize(self):
        self.objRef["_effekseer_path"]=self.path
        self.objRef["_effekseer_scale"]=self.scale
        self.objRef["_effekseer_ignorerot"]= self.ignoreRotation
        self.objRef["_effekseer_enabled"]= self.enabled
        for i in range(0,len(self.inputs)):
            k= "_effekseer_input"+str(i )
            self.objRef[k]=self.inputs[i]
  
    def setIgnoreRotation(self,v):
        self.ignoreRotation=v
        self.serialize()

    def initFromRenderThread(self,effectManager):
        if self.reinit:
            self.reinit=False
            if self.initialized: 
                self.stop(effectManager)
                self.initialized=False

        if not self.initialized:
            self.isNew=True
            if not self.path: return
            self.initialized=True
            self.effect = self.loadEffect(self.path, 1.)


 
    def loadEffect(self,path,size):
        try:
            effectCore = EffekseerEffectCore()

            path=bpy.path.abspath(path)
            root=path[0:path.rindex("/")] if Utils.indexOf(path,"/")!=-1 else ""

            print("Load effect",path)
            b,l=Utils.readBytes(path)
            effectCore.Load(b,l,size)
            # load textures

            print("Load textures")
            textureTypes=(EffekseerTextureType_Color,EffekseerTextureType_Normal,EffekseerTextureType_Distortion)
            for t in range(3):
                for  i in range(effectCore.GetTextureCount(textureTypes[t])):
                    path=effectCore.GetTexturePath(i,textureTypes[t])
                    b,l=Utils.findBytes(root,path)
                    effectCore.LoadTexture(  b,l,i,  textureTypes[t])
                    
            print("Load models")
            for i in range(effectCore.GetModelCount()):
                path=effectCore.GetModelPath(i)
                b,l=Utils.findBytes(root,path)
                effectCore.LoadModel(  b,l,i)

            print("Load materials")
            for i in range(effectCore.GetMaterialCount()):
                path=effectCore.GetMaterialPath(i)
                b,l=Utils.findBytes(root,path)
                effectCore.LoadMaterial(  b,l,i)        

            self.duration=effectCore.GetTermMax()
            return effectCore           
        except Exception as e:
            print("Can't load effect")
            print(e)
        return None
            