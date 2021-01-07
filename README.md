# Effekseer for Blender

*Note: This is currently a prototype and a work in progress that supports only Linux and Windows and it is currently tested mostly on Linux.*

----
----


## Overview

This is a blender 2.8+ addon that renders effekseer effects in blender's viewport. 

The main purpose for this addon is to aid in game map design by showing effekseer particles rendered in blender's Preview viewport. 

The effect's properties are also stored as **Custom properties**  of the object to which the effect is attached, a custom parser can then read those properies from within the model loader in your game engine and load the effect accordingly.

You can see an example implementation for [jMonkeyEngine](https://jmonkeyengine.org) in the addon [jme3-effekseerNative](https://github.com/riccardobl/jme-effekseerNative) or more specifcally here: [EffekseerUtils.java](https://github.com/riccardobl/jme-effekseerNative/blob/master/src/main/java/com/jme/effekseer/EffekseerUtils.java#L315-L350) .

This is built over [this snapshot](https://github.com/riccardobl/Effekseer/tree/ForBlenderAddon) of the rapidly changing [Effekseer master branch](https://github.com/effekseer/Effekseer), you are going to need to use this specific version of the editor for the addon to work as expected. (Binaries are built on github actions and downloadable from [here](https://github.com/riccardobl/Effekseer/releases) )

*The addon can only use efkefc files, so if you intend to load efkproj files (eg. from the Samples folder) you will need to save them as efkefc with the editor.*



## Installation

1. Clone this repo in your addons folder.
2. Enable the addon from blender. 
3. Done.

## Showcase

[![youtube video](https://img.youtube.com/vi/48f-wYo8M1A/0.jpg)](https://www.youtube.com/watch?v=48f-wYo8M1A)


![Screenshot from 2021-01-07 16-12-22](img/Screenshot%20from%202021-01-07%2016-12-22.webp)