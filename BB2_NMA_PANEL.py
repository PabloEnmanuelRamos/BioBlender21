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
from . import BB2_GUI_PDB_IMPORT as PDBIMPORT
from .BB2_PHYSICS_SIM_PANEL import *
from .BB2_MLP_PANEL import *
from .BB2_PDB_OUTPUT_PANEL import *
from .BB2_OUTPUT_PANEL import *
from .BB2_EP_PANEL import *





class BB2_NMA_PANEL(types.Panel):
    bl_label = "BioBlender2 NMA Visualization"
    bl_idname = "BB2_NMA_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    bpy.types.Scene.BBNormalModeAnalysis = bpy.props.EnumProperty(attr="BBNormalModeAnalysis", name="Mode",
                                                                  description="Select a normal mode analysis to show",
                                                                  items=(("0", "1", ""), ("1", "2", ""), ("2", "3", ""),
                                                                         ("3", "4", ""), ("4", "5", ""), ("5", "6", ""),
                                                                         ("6", "7", ""), ("7", "8", ""), ("8", "9", ""),
                                                                         ("9", "10", ""), ("10", "11", ""),
                                                                         ("11", "12", ""), ("12", "13", ""),
                                                                         ("13", "14", ""), ("14", "15", ""),
                                                                         ("15", "16", ""), ("16", "17", ""),
                                                                         ("17", "18", ""), ("18", "19", ""),
                                                                         ("19", "20", "")), default="0")
    bpy.types.Scene.BBNMANbModel = bpy.props.IntProperty(attr="BBNMANbModel", name="NMA steps",
                                                         description="Number of conformations to be calculated in each direction",
                                                         default=6, min=1, max=100, soft_min=1, soft_max=50)
    bpy.types.Scene.BBNMARMSD = bpy.props.FloatProperty(attr="BBNMARMSD", name="RMSD sampling",
                                                        description="RMSD between the given and the farthest conformation",
                                                        default=0.8, min=0.1, max=5.0, soft_min=0.1, soft_max=5.0,
                                                        precision=2, step=1.0)
    bpy.types.Scene.BBNMACutoff = bpy.props.FloatProperty(attr="BBNMACutoff", name="NMA cutoff",
                                                          description="NMA cutoff distance (Å) for pairwise interactions",
                                                          default=15.0, min=0.0, max=25.0, soft_min=1.0, soft_max=25.0)
    bpy.types.Scene.BBNMAGamma = bpy.props.FloatProperty(attr="BBNMAGamma", name="NMA Gamma",
                                                         description="NMA spring constant", default=1.0, min=0.0,
                                                         max=10.0, soft_min=0.1, soft_max=5.0, precision=2, step=1.0)

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        split = layout.split()
        c = split.column()
        c.prop(scene, "BBNormalModeAnalysis")
        c.label("Options:")
        c.prop(scene, "BBNMANbModel")
        c.prop(scene, "BBNMARMSD")
        c.prop(scene, "BBNMACutoff")
        c.prop(scene, "BBNMAGamma")
        c = c.column(align=True)
        c = split.column()
        c.scale_y = 2
        c.operator("ops.bb2_operator_nma")


class bb2_operator_nma(types.Operator):
    bl_idname = "ops.bb2_operator_nma"
    bl_label = "Calculate NMA trajectories (pdb)"
    bl_description = "Calculate Normal Mode Analysis Trajectories"

    def invoke(self, context, event):
        global importReady
        try:
            bpy.context.user_preferences.edit.use_global_undo = False
            computeNormalModeTrajectories()
            bpy.context.user_preferences.edit.use_global_undo = True
        except Exception as E:
            s = "Normal Mode Analysis Calculate Failed: " + str(E)
            print(s)
            return {'CANCELLED'}
        else:
            return {'FINISHED'}


bpy.utils.register_class(bb2_operator_nma)


def computeNormalModeTrajectories():
    name = bpy.context.scene.BBModelRemark
    inputpath = abspath(PDBIMPORT.PDBAddress())
    if os.path.isfile(inputpath):
        modestr = bpy.context.scene.BBNormalModeAnalysis
        mode = int(modestr) + 1
        struct = "--all"
        name = bpy.context.scene.BBModelRemark
        rmsd = bpy.context.scene.BBNMARMSD
        gamma = bpy.context.scene.BBNMAGamma
        cutoff = bpy.context.scene.BBNMACutoff
        nbconfiguration = bpy.context.scene.BBNMANbModel

        outputpath = homePath + "fetched" + os.sep + name + "_" + "Mode" + str(mode) + "_" + struct + "_" + str(rmsd) + "_" + str(nbconfiguration) + ".pdb"

        file = open(outputpath, 'w+')
        file.close()

        if opSystem == "linux":
            command = "chmod 755 %s" % (panel.quotedPath(homePath + "bin" + os.sep + "nma" + os.sep + "nma.py"))
            command = panel.quotedPath(command)
            p = panel.launch(exeName=command, async=False)
        elif opSystem == "darwin":
            command = "chmod 755 %s" % (panel.quotedPath(homePath + "bin" + os.sep + "nma" + os.sep + "nma.py"))
            command = panel.quotedPath(command)
            p = panel.launch(exeName=command, async=False)
        else:
            pyPath = "python"
        command = "%s %s -i %s -o %s -m %d -r %f -n %d %s " % (
            panel.quotedPath(pyPath), panel.quotedPath(homePath + "bin" + os.sep + "nma" + os.sep + "nma.py"),
            panel.quotedPath(inputpath),
            panel.quotedPath(outputpath), mode, rmsd, nbconfiguration, struct)
        p = panel.launch(exeName=command, async=False)
        bpy.context.scene.BBImportPath = outputpath
        PDBIMPORT.importPreview()
    else:
        print("File does not exist !!")




if __name__ == "__main__":
    print("NMA module created")