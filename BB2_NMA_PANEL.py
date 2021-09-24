# -*- coding: utf-8 -*-
# Blender modules
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
from .BB2_PDB_OUTPUT_PANEL import *


class bb2_OT_operator_nma(bpy.types.Operator):
    bl_idname = "ops.bb2_operator_nma"
    bl_label = "Calculate NMA trajectories (pdb)"
    bl_description = "Calculate Normal Mode Analysis Trajectories"

    def invoke(self, context, event):
        global importReady
        try:
            bpy.context.preferences.edit.use_global_undo = False
            computeNormalModeTrajectories()
            bpy.context.preferences.edit.use_global_undo = True
        except Exception as E:
            s = "Normal Mode Analysis Calculate Failed: " + str(E)
            print(s)
            return {'CANCELLED'}
        else:
            return {'FINISHED'}


bpy.utils.register_class(bb2_OT_operator_nma)


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

        outputpath = str(os.environ["BBHome_FETCHED"]) + name + "_" + "Mode" + str(mode) + "_" + struct + "_" + str(rmsd) + "_" + str(nbconfiguration) + ".pdb"

        file = open(outputpath, 'w+')
        file.close()
        if str(os.environ["opSystem"]) == "linux":
            os.environ["pyPath"] = "python"
            if os.path.exists("/usr/bin/python3.9"):
                os.environ["pyPath"] = "python3.9"
            elif os.path.exists("/usr/bin/python3.8"):
                os.environ["pyPath"] = "python3.8"
            elif os.path.exists("/usr/bin/python3"):
                os.environ["pyPath"] = "python3"
            elif os.path.exists("/usr/bin/python"):
                os.environ["pyPath"] = "python"
            elif os.path.exists("/usr/bin/python2"):
                os.environ["pyPath"] = "python2"
            command = "chmod 755 %s" % (panel.quotedPath(str(os.environ["BBHome_BIN_NMA"])))
            command = panel.quotedPath(command)
            p = panel.launch(exeName=command, asynct=False)
        elif str(os.environ["opSystem"]) == "darwin":
            command = "chmod 755 %s" % (panel.quotedPath(str(os.environ["BBHome_BIN_NMA"])))
            command = panel.quotedPath(command)
            p = panel.launch(exeName=command, asynct=False)
        else:
            os.environ["pyPath"] = "python"
        command = "%s %s -i %s -o %s -m %d -r %f -n %d %s " % (
            panel.quotedPath(str(os.environ["pyPath"])), panel.quotedPath(str(os.environ["BBHome_BIN_NMA"])),
            panel.quotedPath(inputpath),
            panel.quotedPath(outputpath), mode, rmsd, nbconfiguration, struct)
        p = panel.launch(exeName=command, asynct=False)
        bpy.context.scene.BBImportPath = outputpath
        PDBIMPORT.importPreview()
    else:
        print("File does not exist !!")


if __name__ == "__main__":
    print("NMA Module")
