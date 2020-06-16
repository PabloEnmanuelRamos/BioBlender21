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
from . import BB2_PANEL_VIEW as panel
from . import BB2_MLP_PANEL as MLP
from .BB2_GUI_PDB_IMPORT import *
from . import BB2_EP_PANEL as EP
from .BB2_PANEL_VIEW import *
from .BB2_PHYSICS_SIM_PANEL import *
from .BB2_MLP_PANEL import *
from .BB2_PDB_OUTPUT_PANEL import *
from .BB2_NMA_PANEL import *
from .BB2_EP_PANEL import *



class BB2_OUTPUT_PANEL(types.Panel):
    bl_label = "BioBlender2 Movie Output"
    bl_idname = "BB2_OUTPUT_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    bpy.types.Scene.BBExportStep = bpy.props.IntProperty(attr="BBExportStep", name="Export Step",
                                                         description="Export step", default=1, min=1, max=100,
                                                         soft_min=1, soft_max=50)
    bpy.types.Scene.BBRecordEP = bpy.props.BoolProperty(attr="BBRecordEP", name="EP Curves (global)",
                                                        description="Do and render EP Visualization")

    def draw(self, context):
        scene = bpy.context.scene
        layout = self.layout
        r = layout.row()
        r.prop(scene, "BBRecordEP")
        r = layout.row()
        r.operator("ops.bb2_operator_movie_refresh")
        r = layout.row()
        for ob in bpy.context.scene.objects:
            try:
                if ob.bb2_objectType == "PDBEMPTY":
                    r.label(str(ob.name))
                    r = layout.row()
                    r.prop(ob, "bb2_outputOptions")
                    r = layout.row()
            except Exception as E:
                print("An error occured in BB2_OUTPUT_PANEL: " + str(E))  # Do nothing...
        r.prop(bpy.context.scene.render, "stamp_note_text", text="Notes")
        r = layout.row()
        r.prop(bpy.context.scene.render, "use_stamp", text="Information Overlay")
        r = layout.row()
        r.prop(bpy.context.scene.world.light_settings, "use_environment_light", text="Ambient Light")
        r = layout.row()
        r.prop(bpy.context.scene.render, "filepath", text="")
        r = layout.row()
        r.prop(bpy.context.scene, "frame_start")
        r = layout.row()
        r.prop(bpy.context.scene, "frame_end")
        r = layout.row()
        r.prop(bpy.context.scene, "BBExportStep")
        r = layout.row()
        stp = bpy.context.scene.BBPDBExportStep
        num = ((bpy.context.scene.frame_end - bpy.context.scene.frame_start) / stp) + 1
        r.label("A total of %d frames will be exported." % (num))
        r = layout.row()
        r.operator("ops.bb2_operator_anim")


class bb2_operator_movie_refresh(types.Operator):
    bl_idname = "ops.bb2_operator_movie_refresh"
    bl_label = "Refresh MOVIE List"
    bl_description = "Refresh MOVIE List"

    def invoke(self, context, event):
        global outputOptions
        for o in bpy.data.objects:
            try:
                if o.bb2_objectType == "PDBEMPTY":
                    pe = copy.copy(o.name)
                    print("pe: " + str(pe))
                    print("outputOption: " + str(o.bb2_outputOptions))
            except Exception as E:
                print("An error occured in bb2_operator_movie_refresh:" + str(E))
        return {'FINISHED'}


bpy.utils.register_class(bb2_operator_movie_refresh)


class bb2_operator_anim(types.Operator):
    bl_idname = "ops.bb2_operator_anim"
    bl_label = "Export Movie"
    bl_description = "Make a movie"

    def invoke(self, context, event):
        try:
            bpy.context.user_preferences.edit.use_global_undo = False
            exportMovie()
            bpy.context.user_preferences.edit.use_global_undo = True
        except Exception as E:
            s = "Export Movie Failed: " + str(E)
            print(s)
            return {'CANCELLED'}
        else:
            return {'FINISHED'}


bpy.utils.register_class(bb2_operator_anim)


def exportMovie():
    step = bpy.context.scene.BBExportStep
    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end
    bpy.context.scene.render.engine = 'BLENDER_RENDER'

    a = time.time()

    pdbPath = os.path.normpath(abspath(bpy.context.scene.render.filepath))
    if opSystem == "linux":
        if not os.path.isdir(pdbPath):
            os.mkdir(abspath(pdbPath))
    elif opSystem == "darwin":
        if not os.path.isdir(pdbPath):
            os.mkdir(abspath(pdbPath))
    else:
        if not os.path.isdir(r"\\?\\" + pdbPath):
            os.mkdir(r"\\?\\" + pdbPath)

    i = start

    # Set-up PDBs...
    PDBdict = {}  # Key: PDBid; Value: PDBEMPTY name
    for p in bpy.data.objects:
        try:
            if p.bb2_objectType == "PDBEMPTY":
                PDBdict[p.bb2_pdbID] = copy.copy(p.name)
        except Exception as E:
            print("Error m01: " + str(E))

    while i <= end:
        bpy.context.scene.frame_start = start
        bpy.context.scene.frame_end = end
        bpy.context.scene.frame_set(i)
        current_frame = bpy.context.scene.frame_current
        # Destroy SURFACE objects
        surfacesDestroyer()
        panel.todoAndviewpoints()
        for pdb in PDBdict:
            bpy.ops.object.select_all(action="DESELECT")
            for o in bpy.data.objects:
                o.select = False
            for o in bpy.data.objects:
                try:
                    if (o.bb2_objectType == "ATOM") and (o.bb2_pdbID == PDBdict[pdb]):
                        o.select = True
                    else:
                        o.select = False
                except Exception as E:
                    print("Error m02: " + str(E))
            # For every PDB ID [ = pdb in PDBdict], calls the right visualization function...
            tmpPDBName = str(PDBdict[pdb])
            tmpPDBobject = bpy.data.objects[tmpPDBName]
            tmpPDBobject.select = True
            bpy.context.scene.objects.active = tmpPDBobject
            try:
                print("tmpPDBobject: " + str(tmpPDBobject.name))
                tmpMode = tmpPDBobject.bb2_outputOptions
                if tmpMode == "0":
                    # Rendering MAIN Atoms
                    bpy.context.scene.BBViewFilter = "1"
                    bpy.context.scene.BBAtomic = "0"
                    bpy.context.scene.BBAtomicMLP = False
                    panel.updateView(residue=bpy.context.scene.objects.active)
                elif tmpMode == "1":
                    # Rendering +SIDE
                    bpy.context.scene.BBViewFilter = "2"
                    bpy.context.scene.BBAtomic = "0"
                    bpy.context.scene.BBAtomicMLP = False
                    panel.updateView(residue=bpy.context.scene.objects.active)
                elif tmpMode == "2":
                    # Rendering +HYD
                    bpy.context.scene.BBViewFilter = "3"
                    bpy.context.scene.BBAtomic = "0"
                    bpy.context.scene.BBAtomicMLP = False
                    panel.updateView(residue=bpy.context.scene.objects.active)
                elif tmpMode == "3":
                    # Rendering Surface
                    bpy.context.scene.BBViewFilter = "4"
                    bpy.context.scene.BBAtomic = "0"
                    bpy.context.scene.BBAtomicMLP = False
                    panel.updateView(residue=bpy.context.scene.objects.active)
                elif tmpMode == "4":
                    # Rendering MLP MAIN
                    bpy.context.scene.BBViewFilter = "1"
                    bpy.context.scene.BBAtomic = "0"
                    bpy.context.scene.BBAtomicMLP = True
                    panel.updateView(residue=bpy.context.scene.objects.active)
                    MLP.atomicMLP(pdb)
                elif tmpMode == "5":
                    # Rendering MLP +SIDE
                    bpy.context.scene.BBViewFilter = "2"
                    bpy.context.scene.BBAtomic = "0"
                    bpy.context.scene.BBAtomicMLP = True
                    panel.updateView(residue=bpy.context.scene.objects.active)
                    MLP.atomicMLP(pdb)
                elif tmpMode == "6":
                    # Rendering MLP +HYD
                    bpy.context.scene.BBViewFilter = "3"
                    bpy.context.scene.BBAtomic = "0"
                    bpy.context.scene.BBAtomicMLP = True
                    panel.updateView(residue=bpy.context.scene.objects.active)
                    MLP.atomicMLP(pdb)
                elif tmpMode == "7":
                    # Rendering MLP SURFACE
                    bpy.context.scene.BBViewFilter = "4"
                    bpy.context.scene.BBAtomic = "1"
                    MLP.mlp(pdb, True)
                    MLP.mlpRender(pdb)
            except Exception as E:
                print("Error m03: " + str(E))
        # ... then, if EP is checked, performs a global EP visualization
        try:
            if bpy.context.scene.BBRecordEP:
                EP.scenewideEP(animation=True)
                step = 1  # EP animation should not skip steps, due to particles behavior
        except Exception as E:
            print("Error m04: " + str(E))
        # render frame
        current_frame = i
        bpy.context.scene.frame_current = 1
        bpy.context.scene.frame_start = i
        bpy.context.scene.frame_end = i
        bpy.context.scene.frame_current = i
        bpy.ops.render.render(animation=True)
        panel.todoAndviewpoints()
        # Next frame
        i += step
    # clean up
    if bpy.context.scene.BBRecordEP:
        for o in bpy.data.objects:
            if ("Curve" == o.name[0:5] or "Emitter" == o.name[0:7]) and (o.parent != bpy.data.objects["Empty_Lines"]):
                o.parent = bpy.data.objects["Empty_Lines"]

    bpy.context.scene.frame_set(start)
    bpy.context.scene.frame_start = start
    bpy.context.scene.frame_end = end
    print(time.time() - a)


def surfacesDestroyer():
    for s in bpy.data.objects:
        s.select = False
        try:
            if s.bb2_objectType == "SURFACE":
                s.select = True
                bpy.context.scene.objects.active = s
                bpy.ops.object.delete(use_global=False)
        except Exception as E:
            print("Error m05: " + str(E))

def ExistEP():
    for b in bpy.context.scene.objects:
        if b.name.split()[0] == "CurveObj":
            return True
    return False


if __name__ == "__main__":
    print("OUTPUT_MOVIE module created")