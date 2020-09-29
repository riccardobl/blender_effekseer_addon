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


    def stop(self,effectManager):
        if self.effectHandle:
            effectManager.Stop(self.effectHandle)

    def update(self,effectManager,wasFrameUpdated,t):
        self.initFromRenderThread(effectManager)

        if not self.initialized: return
      
        exists=self.effectHandle!=None and effectManager.Exists(self.effectHandle)
        if not(exists) and wasFrameUpdated:
            self.effectHandle=effectManager.Play(self.effect)

        if exists:
            transformMatrix=self.objRef.matrix_world

            loc, rot, scale = transformMatrix.decompose()
            scale=Utils.swizzleScale(scale)
            loc=Utils.swizzleLoc(loc)
            
            scale*=self.getScale()

            if  self.ignoreRotation:
                rot=mathutils.Quaternion()
            else:
                rot=Utils.swizzleRot(rot)

            transformMatrix =  Utils.toMatrix(loc,rot,scale)
            


            effectManager.SetEffectTransformMatrix(self.effectHandle,*Utils.getArrayFromMatrix(transformMatrix,True,3))

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
        self.objRef["_effekseer_ignorerot"]=self.ignoreRotation
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
            if not self.path: return
            self.initialized=True
            self.effect = self.loadEffect(self.path, 1.)


 
    def loadEffect(self,path,size):
        effectCore = EffekseerEffectCore()

        root=path[0:path.rindex("/")] if Utils.indexOf(path,"/")!=-1 else ""

        print("Load effect")
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

        return effectCore           
            