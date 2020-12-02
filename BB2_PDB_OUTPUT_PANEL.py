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
from . import BB2_GUI_PDB_IMPORT as ImpPDB
from .BB2_PANEL_VIEW import *
from .BB2_MLP_PANEL import *
from .BB2_EP_PANEL import *

class bb2_OT_operator_export_pdb(bpy.types.Operator):
    bl_idname = "ops.bb2_operator_export_pdb"
    bl_label = "Export PDB"
    bl_description = "Export current view to PDB"

    def invoke(self, context, event):
        try:
            if (bpy.context.view_layer.objects.active.bb2_objectType == "ATOM") or (bpy.context.view_layer.objects.active.bb2_objectType == "PDBEMPTY"):
                context.preferences.edit.use_global_undo = False
                selectedPDBidS = []
                try:
                    if (bpy.context.view_layer.objects.active.bb2_pdbID not in selectedPDBidS) and ((bpy.context.view_layer.objects.active.bb2_objectType == "ATOM") or (bpy.context.view_layer.objects.active.bb2_objectType == "PDBEMPTY")):
                        t = copy.copy(bpy.context.view_layer.objects.active.bb2_pdbID)
                        selectedPDBidS.append(t)
                except Exception as E:
                    str1 = str(E)  # Do not print...
                context.preferences.edit.use_global_undo = False
                for id in selectedPDBidS:
                    tID = copy.copy(id)
                    for o in bpy.data.objects:
                        try:
                            if (o.bb2_pdbID == tID) and (o.bb2_objectType == "PDBEMPTY"):
                                tmpName = copy.copy(str(o.name))
                                exportPDBSequence(tmpName, tID)
                        except Exception as E:
                            print("PDB seq error: " + str(E))
                context.preferences.edit.use_global_undo = True
            else:
                print("No PDB Empty or Atom selected")
        except Exception as E:
            s = "Export PDB Failed: " + str(E)
            print(s)
            return {'CANCELLED'}
        else:
            return {'FINISHED'}


bpy.utils.register_class(bb2_OT_operator_export_pdb)


def trueSphereOrigin(object):
    tmpSphere = bpy.data.objects[object.name]
    coord = [(object.matrix_world[0])[3], (object.matrix_world[1])[3], (object.matrix_world[2])[3]]
    return coord


def exportPDBSequence(curPDBpath="", tID=0):
    step = bpy.context.scene.BBPDBExportStep
    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'

    a = time.time()

    cu = bpy.context.scene.render.filepath + "_" + ((curPDBpath.split("."))[0]) + ".pdb"
    pdbPath = abspath(cu)

    print("=======outPath = " + str(pdbPath))
    with open(pdbPath, "w") as outFile:
        i = start
        while i <= end:
            bpy.context.scene.frame_set(i)
            # PRINT MODEL n
            if i < 10:
                currentModelString = "MODEL " + "       " + str(i)
            elif 9 < i < 100:
                currentModelString = "MODEL " + "      " + str(i)
            elif 99 < i < 1000:
                currentModelString = "MODEL " + "     " + str(i)
            else:
                currentModelString = "MODEL " + "    " + str(i)
            outFile.write(currentModelString + "\n")
            for o in bpy.data.objects:
                try:
                    if (o.bb2_pdbID == tID) and (o.bb2_objectType == "ATOM"):
                        loc = trueSphereOrigin(o)
                        info = o.BBInfo
                        x = "%8.3f" % loc[0]
                        y = "%8.3f" % loc[1]
                        z = "%8.3f" % loc[2]
                        # convert line to pdbstring class
                        line = ImpPDB.PDBString(info)
                        # clear location column
                        line = line.set(30, "                         ")
                        # insert new location
                        line = line.set(30, x)
                        line = line.set(38, y)
                        line = line.set(46, z)
                        outFile.write(line + "\n")
                except Exception as E:
                    print("An error occured while exporting PDB sequence: " + str(E))
            outFile.write("ENDMDL" + "\n")
            i += step
        outFile.write("ENDMDL" + "\n")
    # clean up
    bpy.context.scene.frame_set(start)
    bpy.context.scene.frame_start = start
    bpy.context.scene.frame_end = end
    print(time.time() - a)


if __name__ == "__main__":
    print("PDB_OUTPUT module created")