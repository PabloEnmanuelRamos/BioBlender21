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
from . import BB2_GUI_PDB_IMPORT as ImportPDB
from . import BB2_MLP_PANEL as MLP

global NamePDB
NamePDB = ""
currentActiveObj = ""
oldActiveObj = ""
activeModelRemark = ""
viewFilterOld = ""


class bb2_OT_view_panel_update(bpy.types.Operator):
    bl_idname = "ops.bb2_view_panel_update"
    bl_label = "Show Surface"
    bl_description = "Show Surface model"

    def invoke(self, context, event):
        try:
            if bpy.context.view_layer.objects.active:
                updateView(residue=bpy.context.view_layer.objects.active)
        except Exception as E:
            s = "Generate Surface Failed: " + str(E)
            print(s)
            return {'CANCELLED'}
        else:
            return {'FINISHED'}


bpy.utils.register_class(bb2_OT_view_panel_update)


# depending on view mode, selectively hide certain object based on atom definition
def updateView(residue=None, verbose=False):
    selectedPDBidS = []
    idn = ""
    for b in bpy.context.scene.objects:
        if bpy.context.view_layer.objects.active == b:
            try:
                if b.bb2_pdbID not in selectedPDBidS:
                    t = copy.copy(b.bb2_pdbID)
                    idn = str(copy.copy(b.name))
                    selectedPDBidS.append(t)
            except Exception as E:
                str1 = str(E)  # Do not print...
    viewMode = bpy.context.scene.BBViewFilter
    # select amino acid by group
    if residue:
        # skip none atomic object
        if residue.BBInfo:
            seq = ImportPDB.PDBString(residue.BBInfo).get("chainSeq")
            id = ImportPDB.PDBString(residue.BBInfo).get("chainID")
            for o in bpy.data.objects:
                if o.BBInfo:
                    if (ImportPDB.PDBString(o.BBInfo).get("chainSeq") == seq) and (ImportPDB.PDBString(o.BBInfo).get("chainID") == id):
                        bpy.data.objects[o.name].select_set(True)
                    else:
                        bpy.data.objects[o.name].select_set(False)
    # ================================= SURFACES GENERATION - START ==============================
    # Check if there are SURFACES in the Scene...
    existingSurfaces = []
    for s in bpy.data.objects:
        if s.BBInfo:
            if s.bb2_objectType == "SURFACE":
                existingSurfaces.append(s.name)
    if viewMode == "4" and not Exist(idn.split(".")[0]):
        # If there are not surfaces in Scene...
        if not existingSurfaces:
            # generate surface if does not exist... a different Surface for EVERY pdbID selected...
            # Deselect all; iteratively select objects whose IDs are in selectedPDBidS and launch setup and surface
            for id in selectedPDBidS:
                bpy.ops.object.select_all(action="DESELECT")
                for o in bpy.data.objects:
                    o.select_set(False)
                for obj in bpy.context.scene.objects:
                    try:
                        if obj.bb2_pdbID == id:
                            obj.select_set(True)
                    except Exception as E:
                        str2 = str(E)  # Do not print...
                tID = copy.copy(id)
                setup(setupPDBid=tID)
                print("first setup made")
                surface(sPid=tID)
                print("surface made")
        else:
            # unhide surface if it's hidden
            for ob in existingSurfaces:
                if ob.hide_viewport:
                    ob.hide_viewport = False
                    ob.hide_render = False
        todoAndviewpoints()
    # ================================= SURFACES GENERATION - END ==============================
    else:
        # hide surface if already exist
        if existingSurfaces:
            for o in existingSurfaces:
                bpy.data.objects[o].hide_viewport = True
                bpy.data.objects[o].hide_render = True
    # Check for hiding / reveal objects in Scene
    for obj in bpy.context.scene.objects:
        try:
            if obj.bb2_pdbID in selectedPDBidS:
                obj.hide_viewport = False
                obj.hide_render = False
                # obj.draw_type = "TEXTURED"
                # if re.search("#", obj.name):
                line = obj.BBInfo
                line = ImportPDB.PDBString(line)
                elementName = line.get("element")
                atomName = line.get("name")
                # hide all
                if viewMode == "0":
                    obj.hide_viewport = True
                    obj.hide_render = True
                # Main Chain Only
                elif viewMode == "1":
                    if not (atomName == N or atomName == C or (atomName == CA and elementName != CA) or (
                            atomName in NucleicAtoms) or (atomName in NucleicAtoms_Filtered)):
                        obj.hide_viewport = True
                        obj.hide_render = True
                # Main Chain and Side Chain Only
                elif (viewMode == '2') and (elementName == H or obj.bb2_objectType == "SURFACE"):
                    obj.hide_viewport = True
                    obj.hide_render = True
                # Main Chain and Side Chain Only and H, everything.
                elif viewMode == "3" and obj.bb2_objectType == "SURFACE":
                    obj.hide_viewport = True
                    obj.hide_render = True
                elif viewMode == '4':
                    obj.hide_viewport = False
                    obj.hide_render = False
        except Exception as E:
            str5 = str(E)
            print(str5)


def setup(verbose=False, clear=True, setupPDBid=0):
    # PDB Path is retrieved from parent EMPTY
    pE = None
    global NamePDB
    NamePDB = " "
    for o1 in bpy.context.scene.objects:
        try:
            if o1.bb2_pdbID == setupPDBid:
                if o1.bb2_objectType == "PDBEMPTY":
                    pE = copy.copy(o1.name)
                    NamePDB = MLP.NamePDBMLP(setupPDBid)
        except Exception as E:
            str3 = str(E)  # Do not print...
            print("Setup Error " + str3)
    print("pE: " + str(pE))
    PDBPath = abspath(bpy.data.objects[pE].bb2_pdbPath)
    print("pdppath: " + str(PDBPath))

    if clear:
        if opSystem == "linux":
            if os.path.isdir(quotedPath(homePath + "tmp" + os.sep + NamePDB + os.sep)):
                shutil.rmtree(quotedPath(homePath + "tmp" + os.sep + NamePDB + os.sep))
                os.mkdir(quotedPath(homePath + "tmp" + os.sep + NamePDB + os.sep))
            else:
                os.mkdir(quotedPath(homePath + "tmp" + os.sep + NamePDB + os.sep))
        elif opSystem == "darwin":
            if os.path.isdir(quotedPath(homePath + "tmp" + os.sep + NamePDB + os.sep)):
                shutil.rmtree(quotedPath(homePath + "tmp" + os.sep + NamePDB + os.sep))
                os.mkdir(quotedPath(homePath + "tmp" + os.sep + NamePDB + os.sep))
            else:
                os.mkdir(quotedPath(homePath + "tmp" + os.sep + NamePDB + os.sep))
        else:
            if os.path.isdir(r"\\?\\" + homePath + "tmp" + os.sep + NamePDB + os.sep):
                print("There is a TMP folder!")
            else:
                # os.mkdir(r"\\?\\" + homePath+"tmp" + os.sep)
                print("Trying to making dir on Win (no TMP folder)...")
                os.mkdir(r"\\?\\" + homePath + "tmp" + os.sep + NamePDB)

    if opSystem == "linux":
        shutil.copy(PDBPath, quotedPath(homePath + "tmp" + os.sep + NamePDB + os.sep + "original.pdb"))
    elif opSystem == "darwin":
        shutil.copy(PDBPath, quotedPath(homePath + "tmp" + os.sep + NamePDB + os.sep + "original.pdb"))
    else:
        print("Precopy")
        shutil.copy(r"\\?\\" + PDBPath, r"\\?\\" + homePath + "tmp" + os.sep + NamePDB + os.sep + "original.pdb")

    print("Exporting PDB...")
    exportPDB(path=homePath + "tmp" + os.sep + NamePDB + os.sep + "tmp.pdb", tag=bpy.data.objects[pE].name.split("#")[0], sPid=setupPDBid)

    print("Setup is complete!")


# export scene to PDB file; if no path is specified, it writes to tmp.pdb
def exportPDB(path=homePath + "tmp" + os.sep + NamePDB + os.sep + "tmp.pdb", tag=None, verbose=False, sPid=None):
    print("=============== exporting PDB")
    print("Exporting model '%s' to %s" % (tag, path))

    outPath = abspath(path)
    print("=======outPath = " + str(outPath))
    with open(outPath, "w") as outFile:
        for o in bpy.data.objects:
            try:
                if o.bb2_pdbID == sPid and o.bb2_objectType == "ATOM":
                    loc = o.location
                    info = o.BBInfo
                    x = "%8.3f" % loc[0]
                    y = "%8.3f" % loc[1]
                    z = "%8.3f" % loc[2]
                    # convert line to pdbstring class
                    line = ImportPDB.PDBString(info)
                    # clear location column
                    line = line.set(30, "                         ")
                    # insert new location
                    line = line.set(30, x)
                    line = line.set(38, y)
                    line = line.set(46, z)
                    outFile.write(line + "\n")
            except Exception as E:
                str4 = str(E)
                print("exportPDB Error " + str4)
        outFile.write("ENDMDL" + "\n")


# Import the surface generated from PyMol
def surface(sPid=0, optName=""):
    res = bpy.context.scene.BBMLPSolventRadius
    quality = "1"

    try:
        oPath = homePath + "tmp" + os.sep + NamePDB + os.sep + "tmp.pdb"
        f = open(oPath, "r")
        lines = f.readlines()
        lineCounter = 0
        for line in lines:
            if line.startswith("ATOM"):
                line = line.replace("1+", "  ")
                line = line.replace("1-", "  ")
            lines[lineCounter] = line
            lineCounter = lineCounter + 1
        f.close()
        f = open(oPath, "w")
        f.writelines(lines)
        f.close()
    except Exception as E:
        s = "Unable to fix tmp.pdb: " + str(E)
        print(s)

    tmpPathO = homePath + "tmp" + os.sep + MLP.NamePDBMLP(sPid) + os.sep + "surface.pml"
    tmpPathL = "load " + homePath + "tmp" + os.sep + MLP.NamePDBMLP(sPid) + os.sep + "tmp.pdb" + "\n"
    tmpPathS = "save " + homePath + "tmp" + os.sep + MLP.NamePDBMLP(sPid) + os.sep + "tmp.wrl" + "\n"

    with open(tmpPathO, mode="w") as f:
        f.write("# This file is automatically generated by BioBlender at runtime.\n")
        f.write("# Modifying it manually might not have an effect.\n")
        f.write(tmpPathL)
        f.write('cmd.hide("lines"  ,"tmp")\n')
        f.write('cmd.set("surface_quality"  ,"%s")\n' % quality)
        f.write('cmd.show("surface","tmp")\n')
        f.write('set solvent_radius,' + str(res) + '\n')
        f.write('cmd.reset()\n')
        f.write('cmd.origin(position=[0,0,0])\n')
        f.write('cmd.center("origin")\n')
        f.write(tmpPathS)
        f.write("quit")
    print("Making Surface using PyMOL")
    command = "%s -c -u %s" % (quotedPath(pyMolPath), quotedPath(homePath + "tmp" + os.sep + MLP.NamePDBMLP(sPid) + os.sep + "surface.pml"))

    command = quotedPath(command)
    launch(exeName=command)

    bpy.ops.import_scene.x3d(filepath=homePath + "tmp" + os.sep + MLP.NamePDBMLP(sPid) + os.sep + "tmp.wrl", axis_forward="Y", axis_up="Z")
    try:
        ob = bpy.data.objects['Shape_IndexedFaceSet']
        if optName:
            ob.name = copy.copy(optName)
        else:
            ob.name = "SURFACE_" + NamePDB.split(".")[0] + "_" + getNumFrame()
        ob.bb2_pdbID = copy.copy(sPid)
        ob.bb2_objectType = "SURFACE"
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob

        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.remove_doubles(threshold=0.0001, use_unselected=False)
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.shade_smooth()

        for oE in bpy.data.objects:
            try:
                if (oE.bb2_pdbID == ob.bb2_pdbID) and (oE.bb2_objectType == "PDBEMPTY"):
                    ob.rotation_euler = copy.copy(oE.rotation_euler)
                    ob.location = copy.copy(oE.location)
            except Exception as E:
                print("An error occured while translating and rotating the surface" + str(E))
        ClearLigth(0)
    except Exception as E:
        print("An error occured after importing the WRL Shape_IndexedFaceSet in surface" + str(E))


def quotedPath(stringaInput):
    if stringaInput == "":
        return stringaInput
    else:
        if (stringaInput.startswith("\"")) and (stringaInput.endswith("\"")):
            return stringaInput
    if opSystem == "linux":
        return stringaInput
    elif opSystem == "darwin":
        return stringaInput
    else:
        stringaOutput = "\"" + stringaInput + "\""
        return stringaOutput


# launch app in separate process, for better performance on multithreaded computers
def launch(exeName, asynct=False):
    # try to hide window (does not work recursively)
    if opSystem == "linux":
        istartupinfo = None
    elif opSystem == "darwin":
        istartupinfo = None
    else:
        istartupinfo = subprocess.STARTUPINFO()
        istartupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        istartupinfo.wShowWindow = subprocess.SW_HIDE
    if asynct:
        # if running in async mode, return (the process object) immediately
        return subprocess.Popen(exeName, bufsize=8192, startupinfo=istartupinfo, shell=True)
    else:
        # otherwise wait until process is finished (and return None)
        subprocess.call(exeName, bufsize=8192, startupinfo=istartupinfo, shell=True)
        return None


def select(obj):
    try:
        ob = bpy.data.objects[obj]
        bpy.ops.object.select_all(action="DESELECT")
        for o in bpy.data.objects:
            o.select_set(False)
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
    except Exception as E:
        print("Error Select obj " + str(E))
        return None
    else:
        return ob


def todoAndviewpointsOLD():
    try:
        if "TODO" in bpy.data.objects.keys():
            bpy.ops.object.select_all(action="DESELECT")
            for o in bpy.data.objects:
                o.select_set(False)
            bpy.context.view_layer.objects.active = None
            bpy.data.objects['TODO'].select_set(True)
            bpy.context.view_layer.objects.active = bpy.data.objects['TODO']
            bpy.ops.object.delete(use_global=False)
    except Exception as E:
        print("Warning: TODOs removing not performed properly... " + str(E))
    try:
        if "Viewpoint" in bpy.data.objects.keys():
            bpy.ops.object.select_all(action="DESELECT")
            for o in bpy.data.objects:
                o.select_set(False)
            bpy.context.view_layer.objects.active = None
            bpy.data.objects['Viewpoint'].select_set(True)
            bpy.context.view_layer.objects.active = bpy.data.objects['Viewpoint']
            bpy.ops.object.delete(use_global=False)
    except Exception as E:
        print("Warning: VIEWPOINTs removing not performed properly... " + str(E))


def todoAndviewpoints():
    try:
        for ob in bpy.data.objects:
            if ob.name.startswith("TODO"):
                bpy.ops.object.select_all(action="DESELECT")
                for o in bpy.data.objects:
                    o.select_set(False)
                bpy.context.view_layer.objects.active = None
                ob.select_set(True)
                bpy.context.view_layer.objects.active = ob
                bpy.ops.object.delete(use_global=False)
    except Exception as E:
        print("Warning: TODOs removing not performed properly... " + str(E))
    try:
        for ob in bpy.data.objects:
            if ob.name.startswith("Viewpoint"):
                bpy.ops.object.select_all(action="DESELECT")
                for o in bpy.data.objects:
                    o.select_set(False)
                bpy.context.view_layer.objects.active = None
                ob.select_set(True)
                bpy.context.view_layer.objects.active = ob
                bpy.ops.object.delete(use_global=False)
    except Exception as E:
        print("Warning: VIEWPOINTs removing not performed properly... " + str(E))


def ClearLigth(valor):
    bpy.context.view_layer.objects.active = None
    if valor == 0:
        for ligth in bpy.data.objects:
            ligth.select_set(False)
            if ligth.name[:11] == "DirectLight" and ligth.name != "DirectLight":
                ligth.select_set(True)
    else:
        for ligth in bpy.data.objects:
            ligth.select_set(False)
            if ligth.name[:11] == "DirectLight" and (ligth.name != "DirectLight" and ligth.name != "DirectLight.001"):
                ligth.select_set(True)
    bpy.ops.object.delete()


def getNumFrame():
    global frame
    cifras = len(str(bpy.data.scenes["Scene"].frame_current))
    if cifras == 1:
        frame = "000" + str(bpy.data.scenes["Scene"].frame_current)
    elif cifras == 2:
        frame = "00" + str(bpy.data.scenes["Scene"].frame_current)
    elif cifras == 3:
        frame = "0" + str(bpy.data.scenes["Scene"].frame_current)
    else:
        frame = str(bpy.data.scenes["Scene"].frame_current)
    return frame


def Exist(nm):
    surf = "SURFACE_" + nm + "_" + getNumFrame()
    if surf in bpy.data.objects.keys():
        return True
    return False


if __name__ == "__main__":
    print("PANEL_VIEW module created")
