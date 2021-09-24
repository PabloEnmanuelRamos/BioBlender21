# -*- coding: utf-8 -*-
# Blender modules
# 2020-03-28
import bpy
from bpy import *
import bpy.path
from bpy.path import abspath
from mathutils import *

# Python standard modules
import random
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
from . import BB2_MLP_PANEL as MLP
from .BB2_MLP_PANEL import *
from . import BB2_PDB_OUTPUT_PANEL as PDBOUT


class bb2_OT_operator_ep_clear(types.Operator):
    bl_idname = "ops.bb2_operator_ep_clear"
    bl_label = "Clear EP"
    bl_description = "Clear the EP Visualization"

    def invoke(self, context, event):
        try:
            bpy.context.preferences.edit.use_global_undo = False
            cleanEPObjs()
            bpy.context.preferences.edit.use_global_undo = True
            panel.todoAndviewpoints()
        except Exception as E:
            s = "Clear EP Visualization Failed: " + str(E)
            print(s)
            return {'CANCELLED'}
        else:
            return {'FINISHED'}


bpy.utils.register_class(bb2_OT_operator_ep_clear)


class bb2_OT_operator_ep(types.Operator):
    bl_idname = "ops.bb2_operator_ep"
    bl_label = "Show EP"
    bl_description = "Calculate and Visualize Electric Potential"

    def invoke(self, context, event):
        try:
            bpy.context.preferences.edit.use_global_undo = False
            cleanEPObjs()
            scenewideEP(animation=False)
            bpy.context.scene.BBViewFilter = "4"
            bpy.context.preferences.edit.use_global_undo = True
            panel.todoAndviewpoints()
            if bpy.data.scenes["Scene"].frame_end < 280:
                bpy.data.scenes["Scene"].frame_end = 280
        except Exception as E:
            s = "Generate EP Visualization Failed: " + str(E)
            print(s)
            return {'CANCELLED'}
        else:
            return {'FINISHED'}
        finally:
            # Destroy the surface
            try:
                if "SCENEWIDESURFACE.001" in bpy.data.objects.keys():
                    bpy.ops.object.select_all(action="DESELECT")
                    for o in bpy.data.objects:
                        o.select_set(False)
                    bpy.context.view_layer.objects.active = None
                    bpy.data.objects['SCENEWIDESURFACE.001'].select_set(True)
                    bpy.context.view_layer.objects.active = bpy.data.objects['SCENEWIDESURFACE.001']
                    bpy.ops.object.delete(use_global=False)
                if "SCENEWIDESURFACE" in bpy.data.objects.keys():
                    bpy.ops.object.select_all(action="DESELECT")
                    for o in bpy.data.objects:
                        o.select_set(False)
                    bpy.context.view_layer.objects.active = None
                    bpy.data.objects['SCENEWIDESURFACE'].select_set(True)
                    bpy.context.view_layer.objects.active = bpy.data.objects['SCENEWIDESURFACE']
                    bpy.ops.object.delete(use_global=False)
            except Exception as E:
                print("Warning: SCENEWIDESURFACE removing not performed properly: " + str(E))


bpy.utils.register_class(bb2_OT_operator_ep)


# delete EP related objects
def cleanEPObjs(deletionList=None):
    global epOBJ
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.data.objects:
        if o.name == "Empty_Lines" and deletionList is None:
            o.select_set(True)
        else:
            o.select_set(False)
    # use deletionList if supplied
    if deletionList:
        for obj in deletionList:
            obj.select_set(True)
    # otherwise delete everything in EPOBJ list
    else:
        for list in epOBJ:
            for obj in list:
                obj.select_set(True)
        epOBJ = []
    # call delete operator
    bpy.ops.object.delete()


def scenewideEP(animation):
    global epOBJ, method
    scene = bpy.context.scene

    scenewideSetup()  # In BB1, it was a call to "Setup"; now, Setup is 'per id', so we need a scenewide setup function

    if not animation:
        print("Generating scenewide surface")
        scenewideSurface()

    if (not animation) or (bpy.context.scene.frame_current % 5 == 1):
        print("Generating EP Curves")
        tmpPathOpen = str(os.environ["BBHome_TEMP"]) + "scenewide.pdb"  # former tmp.pdb
        scenewideSurface()

        with open(tmpPathOpen, "r") as file:
            for line in file:
                line = line.replace("\n", "")
                line = line.replace("\r", "")
                line = PDBIMPORT.PDBString(line)
                tag = line.get("tag")

                # if tag is ATOM, load column data
                if tag == "ATOM" or tag == "HETATM":
                    # check for element type
                    if line.get("element") == H:
                        extraCommand = "--assign-only"
                        break

        # select the forcefield
        forcefield = bpy.context.scene.BBForceField
        if forcefield == "0":
            method = "amber"
        elif forcefield == "1":
            method = "charmm"
        elif forcefield == "2":
            method = "parse"
        elif forcefield == "3":
            method = "tyl06"
        elif forcefield == "4":
            method = "peoepb"
        elif forcefield == "5":
            method = "swanson"

        print("Running PDB2PQR")
        if str(os.environ["opSystem"]) == "linux":
            os.chdir(panel.quotedPath(str(os.environ["BBHome_BIN_PDBPQR"])))
        elif str(os.environ["opSystem"]) == "darwin":
            os.chdir(panel.quotedPath(str(os.environ["BBHome_BIN_PDBPQR"])))
        else:
            os.chdir(r"\\?\\" + str(os.environ["BBHome_BIN_PDBPQR"]))
        tmpPathPar1 = str(os.environ["pyPath"])
        tmpPathPar2 = str(os.environ["BBHome_BIN_PDBPQR"]) + "pdb2pqr.py"
        tmpPathPar3 = str(os.environ["BBHome_TEMP"]) + "scenewide.pqr"
        tmpPathPar4 = str(os.environ["BBHome_TEMP"]) + "scenewide.pdb"
        if str(os.environ["opSystem"]) == "linux":
            command = "%s %s --apbs-input --ff=%s %s %s" % (tmpPathPar1, tmpPathPar2, method, tmpPathPar4, tmpPathPar3)
        elif str(os.environ["opSystem"]) == "darwin":
            command = "%s %s --apbs-input --ff=%s %s %s" % (tmpPathPar1, tmpPathPar2, method, tmpPathPar4, tmpPathPar3)
        else:
            command = "%s %s --apbs-input --ff=%s %s %s" % (
                panel.quotedPath(tmpPathPar1), panel.quotedPath(tmpPathPar2), method, panel.quotedPath(tmpPathPar4),
                panel.quotedPath(tmpPathPar3))
        panel.launch(exeName=command)

        print("Running inputgen.py")
        tmp1PathPar1 = str(os.environ["pyPath"])
        tmp1PathPar2 = str(os.environ["BBHome_BIN_PDBPQR"]) + "src" + os.sep + "inputgen.py"
        tmp1PathPar3 = str(os.environ["BBHome_TEMP"]) + "scenewide.pqr"
        if str(os.environ["opSystem"]) == "linux":
            command = "%s %s --istrng=%f --method=auto --space=%f %s" % (
                tmp1PathPar1, tmp1PathPar2, bpy.context.scene.BBEPIonConc, bpy.context.scene.BBEPGridStep, tmp1PathPar3)
        elif str(os.environ["opSystem"]) == "darwin":
            command = "%s %s --istrng=%f --method=auto --space=%f %s" % (
                tmp1PathPar1, tmp1PathPar2, bpy.context.scene.BBEPIonConc, bpy.context.scene.BBEPGridStep, tmp1PathPar3)
        else:
            command = "%s %s --istrng=%f --method=auto --space=%f %s" % (
                panel.quotedPath(tmp1PathPar1), panel.quotedPath(tmp1PathPar2), bpy.context.scene.BBEPIonConc,
                bpy.context.scene.BBEPGridStep, panel.quotedPath(tmp1PathPar3))
        panel.launch(exeName=command)

        print("Running APBS")
        try:
            if str(os.environ["opSystem"]) == "linux":
                shutil.copy(panel.quotedPath(str(os.environ["BBHome_BIN_APBS"]) + "runAPBS.sh"),
                            panel.quotedPath(str(os.environ["BBHome_TEMP"]) + "runAPBS.sh"))
            elif str(os.environ["opSystem"]) == "darwin":
                shutil.copy(panel.quotedPath(str(os.environ["BBHome_BIN_APBS"]) + "darwin_apbs"),
                            panel.quotedPath(str(os.environ["BBHome_TEMP"]) + "darwin_apbs"))
            else:
                shutil.copy(r"\\?\\" + str(os.environ["BBHome_BIN_APBS"]) + "apbs.exe",
                            r"\\?\\" + str(os.environ["BBHome_TEMP"]) + "apbs.exe")
        except Exception as E:
            s = "APBS COPY failed: " + str(E)
            print(s)
        if str(os.environ["opSystem"]) == "linux":
            os.chdir(str(os.environ["BBHome_TEMP"]))
            command = "chmod 755 %s" % (panel.quotedPath(str(os.environ["BBHome_TEMP"]) + "runAPBS.sh"))
            command = panel.quotedPath(command)
            panel.launch(exeName=command)
            command = str(os.environ["BBHome_TEMP"]) + "runAPBS.sh"
        elif str(os.environ["opSystem"]) == "darwin":
            oPath = str(os.environ["BBHome_TEMP"]) + "scenewide.in"
            f = open(oPath, "r")
            lines = f.readlines()
            f.close()
            lines[1] = "    mol pqr " + panel.quotedPath(str(os.environ["BBHome_TEMP"]) + "scenewide.pqr") + "\n"
            f = open(oPath, "w")
            f.writelines(lines)
            f.close()
            command = "chmod 755 %s" % (panel.quotedPath(str(os.environ["BBHome_TEMP"]) + "darwin_apbs"))
            command = panel.quotedPath(command)
            panel.launch(exeName=command)
            command = str(os.environ["BBHome_TEMP"]) + "darwin_apbs" + " " + str(os.environ["BBHome_TEMP"]) + "scenewide.in"
        else:
            oPath = str(os.environ["BBHome_TEMP"]) + "scenewide.in"
            f = open(oPath, "r")
            lines = f.readlines()
            f.close()
            lines[1] = "    mol pqr " + panel.quotedPath(str(os.environ["BBHome_TEMP"]) + "scenewide.pqr") + "\n"
            f = open(oPath, "w")
            f.writelines(lines)
            f.close()
            command = panel.quotedPath(str(os.environ["BBHome_TEMP"]) + "apbs.exe") + " " + panel.quotedPath(
                str(os.environ["BBHome_TEMP"]) + "scenewide.in")
        p = panel.launch(exeName=command, asynct=True)
        print("APBS Ok")

        # sync
        MLP.wait(p)

        # write pot dx pot problems: writes the .dx file in user home path...
        print("============ POT DX POT COPY ================")
        envBoolean = False
        try:
            if str(os.environ["opSystem"]) == "linux":
                dir = str(os.environ["BBHome_TEMP"])
                ext = ".dx"
                listDx = []
                listDx = [x for x in os.listdir(dir) if x.endswith(ext)]
                tmpP = ""
                for f in listDx:
                    if f == "pot.dx":
                        tmpP = panel.quotedPath(str(os.environ["BBHome_TEMP"]) + "pot.dx")
                    elif f[0:3] == "pot":
                        tmpP = panel.quotedPath(str(os.environ["BBHome_TEMP"]) + f)
                if os.path.isfile(tmpP):
                    envBoolean = True
                    print("pot.dx in current directory; won't search in HOME or VIRTUALSTORE folders...")
            elif str(os.environ["opSystem"]) == "darwin":
                tmpP = panel.quotedPath(str(os.environ["BBHome_TEMP"]) + "pot.dx")
                if os.path.isfile(tmpP):
                    envBoolean = True
                    print("pot.dx in current directory; won't search in HOME or VIRTUALSTORE folders...")
        except Exception as E:
            s = "pot.dx output rewrite failed in tmp.in, will search in some folders...: " + str(E)
            print(s)
        if not envBoolean:
            if str(os.environ["opSystem"]) == "linux":
                print("user home: ", os.path.expanduser("~"))
                try:
                    print("BB stays here: ")
                    dir = str(os.environ["BBHome_BIN_PDBPQR"])
                    ext = ".dx"
                    listDx = []
                    listDx = [x for x in os.listdir(dir) if x.endswith(ext)]
                    for f in listDx:
                        if f == "pot.dx":
                            shutil.move(panel.quotedPath(str(os.environ["BBHome_BIN_PDBPQR"]) + "pot.dx"), panel.quotedPath(str(os.environ["BBHome_TEMP"]) + "pot.dx"))
                            shutil.move(panel.quotedPath(str(os.environ["BBHome_BIN_PDBPQR"]) + "io.mc"), panel.quotedPath(str(os.environ["BBHome_TEMP"]) + "io.mc"))
                        elif f[0:3] == "pot":
                            shutil.move(panel.quotedPath(str(os.environ["BBHome_BIN_PDBPQR"]) + "pot.dx"), panel.quotedPath(str(os.environ["BBHome_TEMP"]) + f))
                            shutil.move(panel.quotedPath(str(os.environ["BBHome_BIN_PDBPQR"]) + "io.mc"), panel.quotedPath(str(os.environ["BBHome_TEMP"]) + "io.mc"))
                except Exception as E:
                    s = "pot.dx not found in HOME: " + str(E)
                    print(s)
            elif str(os.environ["opSystem"]) == "darwin":
                print("user home: ", os.path.expanduser("~"))
                try:
                    print("BB stays here: ")
                    shutil.move(panel.quotedPath(str(os.environ["BBHome_BIN_PDBPQR"]) + "pot.dx"), panel.quotedPath(str(os.environ["BBHome_TEMP"]) + "pot.dx"))
                    shutil.move(panel.quotedPath(str(os.environ["BBHome_BIN_PDBPQR"]) + "io.mc"), panel.quotedPath(str(os.environ["BBHome_TEMP"]) + "io.mc"))
                except Exception as E:
                    s = "pot.dx not found in HOME: " + str(E)
                    print(s)
            else:
                try:
                    envHome = str(os.environ['USERPROFILE'])
                    print("envHome: " + envHome)
                    shutil.move(r"\\?\\" + envHome + os.sep + "pot.dx", r"\\?\\" + str(os.environ["BBHome_TEMP"]) + "pot.dx")
                    shutil.move(r"\\?\\" + envHome + os.sep + "io.mc", r"\\?\\" + str(os.environ["BBHom_TEMP"]) + "io.mc")
                    envBoolean = True
                except Exception as E:
                    s = "No pot.dx in HOME: " + str(E)
                    print(s)
                if not envBoolean:
                    print("Win problem; will search in Windows...")
                    try:
                        envHome = "C:" + os.sep + "Windows"
                        print("envHome: " + envHome)
                        shutil.move(envHome + os.sep + "pot.dx", str(os.environ["BBHome_TEMP"]) + "pot.dx")
                        shutil.move(envHome + os.sep + "io.mc", str(os.environ["BBHome_TEMP"]) + "io.mc")
                        envBoolean = True
                    except Exception as E:
                        s = "Windows home failed too; no pot.dx, sorry: " + str(E)
                        print(s)
                if not envBoolean:
                    print("Win problem; will search in AppData - Local - VirtualStore...")
                    try:
                        envHome = str(
                            os.environ['USERPROFILE']) + os.sep + "AppData" + os.sep + "Local" + os.sep + "VirtualStore"
                        print("envHome: " + envHome)
                        shutil.move(envHome + os.sep + "pot.dx", str(os.environ["BBHome_TEMP"]) + "pot.dx")
                        shutil.move(envHome + os.sep + "io.mc", str(os.environ["BBHome_TEMP"]) + "io.mc")
                        envBoolean = True
                    except Exception as E:
                        s = "VirtualStore failed too; no pot.dx, sorry: " + str(E)
                        print(s)
                if not envBoolean:
                    print("Win problem; will search in AppData - Local - VirtualStore - Windows...")
                    try:
                        envHome = str(os.environ['USERPROFILE']) + os.sep + "AppData" + os.sep + "Local" + os.sep + "VirtualStore" + os.sep + "Windows"
                        print("envHome: " + envHome)
                        shutil.move(envHome + os.sep + "pot.dx", str(os.environ["BBHome_TEMP"]) + "pot.dx")
                        shutil.move(envHome + os.sep + "io.mc", str(os.environ["BBHome_TEMP"]) + "io.mc")
                        envBoolean = True
                    except Exception as E:
                        s = "VirtualStore - Windows failed too; no pot.dx, sorry: " + str(E)
                        print(s)
                        print("=========== SORRY: CANNOT FIND POT.DX ============")
        print("Saving obj")
        exportOBJ(str(os.environ["BBHome_TEMP"]) + "scenewide")

        if len(epOBJ) >= maxCurveSet:
            # delete the oldest curve-sets out of the list.
            epOBJ.reverse()
            deletionList = epOBJ.pop()
            cleanEPObjs(deletionList)
            epOBJ.reverse()

        print("Running Scivis")
        if str(os.environ["opSystem"]) == "linux":
            if platform.architecture()[0] == "64bit":
                os.chdir(str(os.environ["BBHome_BIN_SCIVIS"]))
                command = "chmod 755 %s" % (panel.quotedPath(str(os.environ["BBHome_BIN_SCIVIS"]) + "SCIVISLINUX"))
                command = panel.quotedPath(command)
                panel.launch(exeName=command)
                command = "%s %s %s %s %f %f %f %f %f" % (str(os.environ["BBHome_BIN_SCIVIS"]) + "SCIVISLINUX", str(os.environ["BBHome_TEMP"]) + "scenewide.obj", str(os.environ["BBHome_TEMP"]) + "pot.dx", str(os.environ["BBHome_TEMP"]) + "tmp.txt", bpy.context.scene.BBEPNumOfLine / 10, bpy.context.scene.BBEPMinPot, 45, 1, 3)
            else:
                os.chdir(str(os.environ["BBHome_BIN_SCIVIS"]))
                command = "chmod 755 %s" % (
                    panel.quotedPath(str(os.environ["BBHome_BIN_SCIVIS"]) + "SCIVIS"))
                command = panel.quotedPath(command)
                panel.launch(exeName=command)
                command = "%s %s %s %s %f %f %f %f %f" % (str(os.environ["BBHome_BIN_SCIVIS"]) + "SCIVIS",
                                                          str(os.environ["BBHome_TEMP"]) + "scenewide.obj",
                                                          str(os.environ["BBHome_TEMP"]) + "pot.dx",
                                                          str(os.environ["BBHome_TEMP"]) + "tmp.txt",
                                                          bpy.context.scene.BBEPNumOfLine / 10,
                                                          bpy.context.scene.BBEPMinPot, 45, 1, 3)
        elif str(os.environ["opSystem"]) == "darwin":
            command = "chmod 755 %s" % (panel.quotedPath(str(os.environ["BBHome_BIN_SCIVIS"]) + "darwin_SCIVIS"))
            command = panel.quotedPath(command)
            panel.launch(exeName=command)
            command = "%s %s %s %s %f %f %f %f %f" % (str(os.environ["BBHome_BIN_SCIVIS"]) + "darwin_SCIVIS",
                                                      str(os.environ["BBHome_TEMP"]) + "scenewide.obj",
                                                      str(os.environ["BBHome_TEMP"]) + "pot.dx",
                                                      str(os.environ["BBHome_TEMP"]) + "tmp.txt",
                                                      bpy.context.scene.BBEPNumOfLine / 10,
                                                      bpy.context.scene.BBEPMinPot, 45, 1, 3)
        else:
            command = "%s %s %s %s %f %f %f %f %f" % (
                panel.quotedPath(str(os.environ["BBHome_BIN_SCIVIS"]) + "SCIVIS.exe"),
                panel.quotedPath(str(os.environ["BBHome_TEMP"]) + "scenewide.obj"),
                panel.quotedPath(str(os.environ["BBHome_TEMP"]) + "pot.dx"),
                panel.quotedPath(str(os.environ["BBHome_TEMP"]) + "tmp.txt"), bpy.context.scene.BBEPNumOfLine / 10,
                bpy.context.scene.BBEPMinPot, 45, 1, 3)
        panel.launch(exeName=command)

        print("Importing data into Blender")

        if animation:
            list = importEP(str(os.environ["BBHome_TEMP"]) + "tmp.txt", animation=True)
        else:
            list = importEP(str(os.environ["BBHome_TEMP"]) + "tmp.txt", animation=False)

        epOBJ.append(list)

        ob = panel.select("Emitter")

        print("Current frame before if animation: " + str(bpy.context.scene.frame_current))
        if not animation:
            if not bpy.context.screen.is_animation_playing:
                bpy.ops.screen.animation_play()
        # Destroy the surface
        try:
            if "SCENEWIDESURFACE.001" in bpy.data.objects.keys():
                bpy.ops.object.select_all(action="DESELECT")
                for o in bpy.data.objects:
                    o.select_set(False)
                bpy.context.view_layer.objects.active = None
                bpy.data.objects['SCENEWIDESURFACE.001'].select_set(True)
                bpy.context.view_layer.objects.active = bpy.data.objects['SCENEWIDESURFACE.001']
                bpy.ops.object.delete(use_global=False)
            if "SCENEWIDESURFACE" in bpy.data.objects.keys():
                bpy.ops.object.select_all(action="DESELECT")
                for o in bpy.data.objects:
                    o.select_set(False)
                bpy.context.view_layer.objects.active = None
                bpy.data.objects['SCENEWIDESURFACE'].select_set(True)
                bpy.context.view_layer.objects.active = bpy.data.objects['SCENEWIDESURFACE']
                bpy.ops.object.delete(use_global=False)
        except Exception as E:
            print("Warning: SCENEWIDESURFACE removing not performed properly: " + str(E))
    panel.ClearLigth(0)


# import curve description text into Blender
def importEP(path, animation=False):
    global curveCount
    global objList
    lin = False
    if "Empty_Lines" in bpy.data.objects.keys():
        parentEmpty = "Empty_Lines"
        lin = True

    if not lin:
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        bpy.context.view_layer.objects.active.name = "Empty_Lines"
        bpy.context.view_layer.objects.active.bb2_objectType = "CHAINEMPTY"
        bpy.context.view_layer.objects.active.location = (0.0, 0.0, 0.0)
        parentEmpty = bpy.context.view_layer.objects.active.name

    curveCount = 0
    scene = bpy.context.scene
    pts = []
    objList = []
    try:
        materialparticle = bpy.data.materials["Particle"]
    except Exception:
        # read the file once to generate curves
        Directory = str(os.environ["BBHome_DATA"]) + "Particle.blend" + os.sep + "Material" + os.sep
        Path = os.sep + os.sep + "data" + os.sep + "Particle.blend" + os.sep + "Material" + os.sep + "Particle"
        objName = "Particle"

        append_file_to_current_blend(Path, objName, Directory)

    with open(path, "r") as file:
        for file_line in file:
            line = file_line.split()
            if line[0] == "n":
                if curveCount != 0:
                    # for every n encountered creates a new curve
                    cu = bpy.data.curves.new("Curve%3d" % curveCount, "CURVE")
                    ob = bpy.data.objects.new("CurveObj%3d" % curveCount, cu)
                    for x in bpy.data.collections:
                        if x.name == 'Collection':
                            coll = x
                            coll.objects.link(ob)
                    # bpy.context.scene.objects.link(ob)
                    bpy.context.view_layer.objects.active = ob
                    # set all the properties of the curve
                    spline = cu.splines.new("NURBS")
                    cu.dimensions = "3D"
                    cu.use_path = True
                    cu.resolution_u = 1
                    spline.points.add(len(pts) // 4 - 1)
                    spline.points.foreach_set('co', pts)
                    spline.use_endpoint_u = True
                    ob.field.type = "GUIDE"
                    ob.field.use_max_distance = True
                    ob.field.distance_max = 0.05
                    # objList keeps a list of all EP related objects for easy deletion
                    ob.parent = bpy.data.objects[parentEmpty]
                    objList.append(ob)
                    ob.data.bevel_depth = 0.02
                    ob.data.bevel_resolution = 0
                    ob.data.materials.append(bpy.data.materials["Particle"])
                    pts = []
                curveCount += 1
            elif line[0] == "v":
                pts.append(float(line[1]))
                pts.append(float(line[2]))
                pts.append(float(line[3]))
                pts.append(1)

    # read the file again to generate the particle emitter object
    with open(path, "r") as file:
        verts = []
        for line in file:
            # read the first line after each 'n' identifier
            if "n" in line:
                next = file.readline()
                coord = next.split()
                verts.append([float(i) for i in coord[1:]])

        # make mesh
        mesh = bpy.data.meshes.new("Emitter")
        mesh.from_pydata(verts[:-1], [], [])  # [:-1] to fix the off by one error somewhere...
        objList.append(ob)

    return objList


# Convert WRL to OBJ for scivis.exe
def exportOBJ(path):
    vertexData = []  # list of list[3] (wrl vertices data)
    # read wrl file
    with open(path + ".wrl") as wrl:
        found = False
        for line in wrl:
            # skip to coord section of the file
            if not found:
                if "coord" in line:
                    wrl.readline()
                    found = True
            # when in the coord section of the file
            else:
                if "]" not in line:
                    # convert vertexData from string to a list of float
                    entry = line[:-2].split()
                    entryFloat = [float(coord) for coord in entry]
                    vertexData.append(entryFloat)
                else:
                    break

    # write obj file: vertex data
    with open(path + ".obj", mode="w") as obj:
        for entry in vertexData:
            out = "v %f %f %f\n" % (entry[0], entry[1], entry[2])
            obj.write(out)

        # face data
        i = 0
        while i < len(vertexData):
            out = "f %d/%d %d/%d %d/%d\n" % (i + 1, i + 1, i + 2, i + 2, i + 3, i + 3)
            obj.write(out)
            i += 3


def scenewideSetup():
    path = str(os.environ["BBHome_TEMP"]) + "scenewide.pdb"
    # Actually, this is a custom "exportPDB" function, without instructions which were present in original "setup" function
    print("=============== exporting PDB")
    print("Exporting scene to: " + str(path))

    outPath = abspath(path)
    print("=======outPath = " + str(outPath))
    i = 1
    with open(outPath, "w") as outFile:
        for o in bpy.data.objects:
            try:
                if o.bb2_objectType == "ATOM":
                    loc = PDBOUT.trueSphereOrigin(o)
                    info = o.BBInfo
                    x = "%8.3f" % loc[0]
                    y = "%8.3f" % loc[1]
                    z = "%8.3f" % loc[2]
                    # convert line to pdbstring class
                    line = PDBIMPORT.PDBString(info)
                    # Recalculate ATOM id number...
                    line = line.set(1, "           ")
                    if i < 10:
                        tmpString = "ATOM      " + str(i)
                    elif 9 < i < 100:
                        tmpString = "ATOM     " + str(i)
                    elif 99 < i < 1000:
                        tmpString = "ATOM    " + str(i)
                    else:
                        tmpString = "ATOM   " + str(i)
                    line = line.set(0, tmpString)
                    # clear location column
                    line = line.set(30, "                         ")
                    # insert new location
                    line = line.set(30, x)
                    line = line.set(38, y)
                    line = line.set(46, z)
                    outFile.write(line + "\n")
                    i += 1
            except Exception as E:
                str4 = str(E)
                print("An error occured in sceneWideSetup: " + str4)
        outFile.write("ENDMDL" + "\n")
    print("scenewideSetup is complete!")


# Import the surface generated from PyMol
def scenewideSurface():
    res = bpy.context.scene.BBMLPSolventRadius
    quality = "1"

    try:
        oPath = str(os.environ["BBHome_TEMP"]) + "scenewide.pdb"
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
        s = "Unable to fix scenewide.pdb: " + str(E)
        print(s)

    tmpPathO = str(os.environ["BBHome_TEMP"]) + "surface.pml"
    tmpPathL = "load " + str(os.environ["BBHome_TEMP"]) + "scenewide.pdb" + "\n"
    tmpPathS = "save " + str(os.environ["BBHome_TEMP"]) + "scenewide.wrl" + "\n"

    with open(tmpPathO, mode="w") as f:
        f.write("# This file is automatically generated by BioBlender at runtime.\n")
        f.write("# Modifying it manually might not have an effect.\n")
        f.write(tmpPathL)
        f.write('cmd.hide("lines"  ,"scenewide")\n')
        f.write('cmd.set("surface_quality"  ,"%s")\n' % quality)
        f.write('cmd.show("surface","scenewide")\n')
        f.write('set solvent_radius,' + str(res) + '\n')
        f.write('cmd.reset()\n')
        f.write('cmd.origin(position=[0,0,0])\n')
        f.write('cmd.center("origin")\n')
        f.write(tmpPathS)
        f.write("quit")
    print("Making Surface using PyMOL")

    command = "%s -c -u %s" % (panel.quotedPath(str(os.environ["pyMolPath"])), panel.quotedPath(str(os.environ["BBHome_TEMP"]) + "surface.pml"))
    command = panel.quotedPath(command)
    panel.launch(exeName=command)

    bpy.ops.import_scene.x3d(filepath=str(os.environ["BBHome_TEMP"]) + "scenewide.wrl", axis_forward="Y", axis_up="Z")

    try:
        ob = bpy.data.objects["Shape_IndexedFaceSet"]
        ob.name = "SCENEWIDESURFACE"
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
                print("An error occured while translating and rotating the surface")
                print(str(E))
    except Exception as E:
        print("An error occured after importing the WRL Shape_IndexedFaceSet in surface")
        print(str(E))
    panel.ClearLigth(0)


if __name__ == "__main__":
    print("EP module created")
