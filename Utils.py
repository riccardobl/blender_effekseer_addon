import os
import mathutils
yupMatrix=mathutils.Matrix([[1 ,0, 0, 0],[0, 0 ,-1 ,0],[0, 1, 0, 0],[0, 0, 0, 1]])

def fixYUp(mat):
    return mat @ yupMatrix

def getArrayFromMatrix(mat,rowMajor,limit=4):
    m=[]
    for r in   (mat.row if rowMajor else mat.column)[0:limit]:  m.extend(r)
    return m


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


def idOf(obj):
    return id(obj)