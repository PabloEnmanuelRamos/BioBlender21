# Blender modules
# 2020-03-28
import bpy
from bpy import *
import bpy.path
from bpy.path import abspath
from mathutils import *

# Python standard modules
from urllib.parse import urlencode
from urllib.request import *
from html.parser import *
from smtplib import *
from email.mime.text import MIMEText
import time
import platform
import os
import codecs
import base64
from math import *
import pickle
import shutil
import subprocess
import sys
import traceback
import copy

from .BioBlender2 import *
from .BB2_GUI_PDB_IMPORT import *
from . import BB2_PANEL_VIEW as panel
from .BB2_MLP_PANEL import *
from .BB2_PDB_OUTPUT_PANEL import *
from .BB2_OUTPUT_PANEL import *
from .BB2_NMA_PANEL import *
from .BB2_EP_PANEL import *


geList = []


class BB2_PHYSICS_SIM_PANEL(types.Panel):
    bl_label = "BioBlender2 Game Engine Sim"
    bl_idname = "BB2_PHYSICS_SIM_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    bpy.types.Scene.BBDeltaPhysicRadius = bpy.props.FloatProperty(attr="BBDeltaPhysicRadius", name="Radius",
                                                                  description="Value of radius for collisions in physics engine",
                                                                  default=0.7, min=0.1, max=2, soft_min=.1, soft_max=2)
    bpy.types.Scene.BBRecordAnimation = bpy.props.BoolProperty(attr="BBRecordAnimation", name="RecordAnimation",
                                                               description="Use the physics engine to calculate protein motion and record the IPO")

    def draw(self, context):
        global activeObj
        global activeobjOld
        scene = context.scene
        layout = self.layout
        r = layout.row()
        r.operator("ops.bb2_operator_ge_refresh")
        r = layout.row()
        split = r.split(percentage=0.50)
        try:
            for m in geList:
                split.label(str(m))
                split.prop(bpy.context.scene.objects[str(m)].game, "physics_type")
                r = layout.row()
                split = r.split(percentage=0.50)
        except Exception as E:
            print("An error occured in SIM_PANEL.draw while drawing geList")
        r = layout.row()
        split = r.split(percentage=0.50)
        split.prop(scene, "BBRecordAnimation")
        split.prop(scene, "BBDeltaPhysicRadius")
        r = layout.row()
        r.operator("ops.bb2_operator_interactive")


class bb2_operator_interactive(types.Operator):
    bl_idname = "ops.bb2_operator_interactive"
    bl_label = "Run in Game Engine"
    bl_description = "Enter Interactive View Mode"

    def invoke(self, context, event):
        for o in bpy.data.objects:
            try:
                if o.bb2_objectType == "SURFACE":
                    o.select = True
                    bpy.context.scene.objects.active = o
                    bpy.ops.object.delete(use_global=False)
            except Exception as E:
                print("No Shape_IndexedFaceSet in scene (or renamed...) " + str(E))
        try:
            if bpy.context.scene.BBViewFilter == "4":
                bpy.context.scene.BBViewFilter = "3"
                panel.updateView()
            geStart()
        except Exception as E:
            s = "Start Game Failed: " + str(E)
            print(s)
            return {'CANCELLED'}
        else:
            return {'FINISHED'}


bpy.utils.register_class(bb2_operator_interactive)


class bb2_operator_ge_refresh(types.Operator):
    bl_idname = "ops.bb2_operator_ge_refresh"
    bl_label = "Refresh GE List"
    bl_description = "Refresh GE List"

    def invoke(self, context, event):
        global geList
        geList = []
        for o in bpy.data.objects:
            try:
                bpy.context.scene.render.engine = 'BLENDER_GAME'
                if o.bb2_objectType == "PDBEMPTY":
                    pe = copy.copy(o.name)
                    geList.append(pe)
            except Exception as E:
                str7 = str(E)  # Do nothing...
                print("Refresh GE List Error" + str7)
        return {'FINISHED'}


bpy.utils.register_class(bb2_operator_ge_refresh)


def geStart():
    tmpFPS = bpy.context.scene.render.fps
    bpy.context.scene.render.fps = 1
    bpy.context.scene.game_settings.fps = bpy.context.scene.render.fps
    bpy.context.scene.game_settings.physics_engine = "BULLET"
    bpy.context.scene.game_settings.logic_step_max = 1
    if bpy.context.vertex_paint_object:
        bpy.ops.paint.vertex_paint_toggle()

    bpy.context.scene.render.engine = 'BLENDER_GAME'
    bpy.context.scene.game_settings.physics_gravity = 0.0

    for i, obj in enumerate(bpy.data.objects):
        if obj.bb2_objectType == 'ATOM':
            obj.game.radius = bpy.context.scene.BBDeltaPhysicRadius

    # Setting dynamic-static type...
    for m in geList:
        tmpEmpty = bpy.data.objects[str(m)]
        tmpID = copy.copy(tmpEmpty.bb2_pdbID)
        for o in bpy.data.objects:
            try:
                if (o.bb2_pdbID == tmpID) and (o.bb2_objectType == 'ATOM'):
                    tmpType = copy.copy(tmpEmpty.game.physics_type)
                    o.game.physics_type = str(tmpType)
                    #if str(o.BBInfo.split()[2])[:1] != "H":
                       # o.game.radius = bpy.context.scene.BBDeltaPhysicRadius
            except Exception as E:
                str8 = str(E)
                print("geStart() Error " + str8)
        tmpEmpty.game.physics_type = "NO_COLLISION"

    # START!
    bpy.ops.view3d.game_start()
    bpy.context.scene.render.fps = tmpFPS

# record physics engine movement to FCurve
def recorder():
    # tread softly, for you tread on two API
    from bge import logic
    from bge import render
    from bpy import data
    from bpy import context
    from bpy import ops

    if bpy.context.scene.BBRecordAnimation:
        cont = logic.getCurrentController()
        scene = logic.getCurrentScene()
        own = cont.owner

        # In the original (v0.6v), Timer was a float, but there was no increment on this value,
        # so no steps forwards, just frame 1... now, in Empty Set, there is an always actuator which
        # increments (frame after frame) the value...
        time = own["timer"]
        # record to a new region of the timeline
        offset = 200 + bpy.context.scene.frame_end

        # for all object
        for bgeOBJ in scene.objects:
            try:
                # lookup BPY object from  BGE object name
                bpyOBJ = bpy.data.objects[bgeOBJ.name]
            except Exception as E:
                print("GE_Recorder problem: " + str(E))
                continue

            # ignore non-atom object (lamps, cameras, etc)
            if bpyOBJ.BBInfo:
                bpyOBJ.location = bgeOBJ.position
                bpyOBJ.select = True

        # jump to new position for recording
        bpy.context.scene.frame_current = int(time + offset)
        # insert keyframe
        bpy.ops.anim.keyframe_insert_menu(type="LocRotScale")
        # jump back to the playback position
        bpy.context.scene.frame_current = int(time)

        # end game if done
        if time > bpy.context.scene.frame_end:
            logic.endGame()
        else:
            print("\rRecording protein motion %.0f%%" % (time / bpy.context.scene.frame_end * 100), end="")

if __name__ == "__main__":
    print("PHYSICS_SIM module created")