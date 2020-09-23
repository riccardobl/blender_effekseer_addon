
bl_info = {
        "name": "Effekseer",
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
from .ProjectionMatrix import *
import mathutils

class State :
    effectManager=None
    effect=None
    effectHandle=None
    lastTime=0

def getArrayFromMatrix(mat,rowMajor,limit=4):
    m=[]
    for r in   (mat.row if rowMajor else mat.column)[0:limit]:  m.extend(r)
    return m

def onRender(x):
    print("After render")
    bgl.glClearColor(1,0,0,1)                # define color used to clear buffers 
    bgl.glClear(bgl.GL_COLOR_BUFFER_BIT)   

def onDraw(state):
    if state.effectManager==None: 
        EffekseerBackendCore_InitializeAsOpenGL()
        
        state.effectManager = EffekseerManagerCore()
        state.effectManager.Initialize(8000)
        
        state.effect = loadEffect("/home/riccardo/Desktop/jme-effekseerNative/src/test/resources/effekts/Pierre/Flame.efkefc", 1.)


    yupMatrix=mathutils.Matrix([[1 ,0, 0, 0],[0, 0 ,-1 ,0],[0, 1, 0, 0],[0, 0, 0, 1]])
    yupMatrixInverted=yupMatrix.copy()
    yupMatrixInverted.invert()

    viewMatrix=gpu.matrix.get_model_view_matrix()
    viewMatrix  = viewMatrix 
    state.effectManager.SetCameraMatrix(*getArrayFromMatrix(viewMatrix ,True)  )

    projectionMatrix=gpu.matrix.get_projection_matrix()
    projectionMatrix = projectionMatrix 
    state.effectManager.SetProjectionMatrix(*getArrayFromMatrix(projectionMatrix,True )  )

    frame=bpy.context.scene.frame_current
    time=   ((frame )/ max(1.0, float(bpy.context.scene.render.fps)))
    time=time / (1.0/ 60.0)
    
    update=False
    if  state.lastTime!=time:
        state.lastTime=time
        update=True

    exists=state.effectHandle!=None and state.effectManager.Exists(state.effectHandle)
    if not(exists) and update:
        state.effectHandle=state.effectManager.Play(state.effect)

    if exists:
        transformMatrix=bpy.context.scene.objects["Cube"].matrix_world  @ yupMatrix
        state.effectManager.SetEffectTransformMatrix(state.effectHandle,*getArrayFromMatrix(transformMatrix,True,3))
    
    if update:
        state.effectManager.BeginUpdate()
        state.effectManager.UpdateHandleToMoveToFrame(state.effectHandle,time)
        state.effectManager.EndUpdate()

    state.effectManager.DrawBack()
    state.effectManager.DrawFront()


def normalizePath(*parts):
    path=""

    for part in parts:  path+="/"+part.replace("\\", "/")
    
    path=os.path.normpath(path)
    path=path.replace("\\", "/")
        
    sStr=0
    while(path.startswith("../",sStr)): sStr+=3
    path=path[sStr:]

    if(path.startswith("/")):path=path[1:]

    return path

def indexOf(s,v):
    try:
        return s.index(v)
    except:
        return -1


def guessPossibleRelPaths( root, opath):
    root=normalizePath(root)

    path=opath
    path=normalizePath(path)   
        
    print("Guesses for "+opath+" normalized "+path+" in root "+root)

    paths=[] 

    paths.append(path)
    paths.append(normalizePath(root,path))

    pathsNoRoot=[]

    while True :
        i=indexOf(path,"/")
        if i==-1: break
        path=path[i+1:]
        if(path==""): break
        pathsNoRoot.append(path)
        paths.append(normalizePath(root,path))
        
    paths.extend(pathsNoRoot)


    for p in paths:print(" > "+p)
    return paths

def readBytes(path):
    f=open(path,"rb")
    bb=f.read()
    f.close()
    l=len(bb)
    print(path,l," bytes")        
    return bb,l

def findBytes(root,path):
    paths=guessPossibleRelPaths(root,path)
    for path in paths:
        if not os.path.exists(path):
            print("Path "+path+" invalid. Skip.")
            continue
        print("Found ",path)
        return readBytes(path)
    return None,0

def loadEffect(path,size):
    effectCore = EffekseerEffectCore()

    root=path[0:path.rindex("/")] if indexOf(path,"/")!=-1 else ""

    print("Load effect")
    b,l=readBytes(path)
    effectCore.Load(b,l,size)
    # load textures

    print("Load textures")
    textureTypes=(EffekseerTextureType_Color,EffekseerTextureType_Normal,EffekseerTextureType_Distortion)
    for t in range(3):
         for  i in range(effectCore.GetTextureCount(textureTypes[t])):
             path=effectCore.GetTexturePath(i,textureTypes[t])
             b,l=findBytes(root,path)
             effectCore.LoadTexture(  b,l,i,  textureTypes[t])
             
    print("Load models")
    for i in range(effectCore.GetModelCount()):
        path=effectCore.GetModelPath(i)
        b,l=findBytes(root,path)
        effectCore.LoadModel(  b,l,i)

    print("Load materials")
    for i in range(effectCore.GetMaterialCount()):
        path=effectCore.GetMaterialPath(i)
        b,l=findBytes(root,path)
        effectCore.LoadMaterial(  b,l,i)        

    return effectCore

drawHandler=None
def register():
    print("Load Effekseer renderer")
    global drawHandler
    args=(State(),)
    drawHandler=bpy.types.SpaceView3D.draw_handler_add(onDraw,args,"WINDOW","POST_VIEW")
    # bpy.app.handlers.render_complete.append(onRender)
    
def unregister():
    global drawHandler
    if drawHandler!=None:
        drawHandler=None
        bpy.types.SpaceView3D.draw_handler_remove(drawHandler,"WINDOW")


if __name__ == '__main__':
    register()
