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
from . import BB2_PANEL_VIEW as panel

global namemlp
namemlp = ""

class bb2_OT_operator_atomic_mlp(bpy.types.Operator):
    bl_idname = "ops.bb2_operator_atomic_mlp"
    bl_label = "Atomic MLP"
    bl_description = "Atomic MLP"

    def invoke(self, context, event):
        try:
            selectedPDBidS = []
            try:
                if bpy.context.view_layer.objects.active.bb2_pdbID not in selectedPDBidS:
                    t = copy.copy(bpy.context.view_layer.objects.active.bb2_pdbID)
                    selectedPDBidS.append(t)
            except Exception as E:
                str1 = str(E)  # Do not print...
                print("AtomicMLP ERROR 1" + str1)
            context.preferences.edit.use_global_undo = False
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
                        print("AtomicMLP ERROR 2" + str2)
                tID = copy.copy(id)
                atomicMLP(tID)
            context.preferences.edit.use_global_undo = True
        except Exception as E:
            s = "Generate Atomic MLP visualization Failed: " + str(E)
            print(s)
            return {'CANCELLED'}
        else:
            return {'FINISHED'}


bpy.utils.register_class(bb2_OT_operator_atomic_mlp)


def atomicMLP(tID):
    for obj in bpy.data.objects:
        try:
            if (obj.bb2_pdbID == tID) and (obj.bb2_objectType == "ATOM"):
                aminoName = ImportPDB.PDBString(obj.BBInfo).get("aminoName")
                name = ImportPDB.PDBString(obj.BBInfo).get("name")
                material_this = ImportPDB.retrieve_fi_materials(am_name=aminoName, at_name=name)
                obj.material_slots[0].material = bpy.data.materials[material_this]
                bpy.context.scene.BBAtomicMLP = True
        except Exception as E:
            print(str(E))
    print("Atomic MLP Color set")



class bb2_OT_operator_mlp(bpy.types.Operator):
    bl_idname = "ops.bb2_operator_mlp"
    bl_label = "Show MLP on Surface"
    bl_description = "Calculate Molecular Lipophilicity Potential on surface"

    def invoke(self, context, event):
        try:
            context.preferences.edit.use_global_undo = False
            selectedPDBidS = []
            try:
                if bpy.context.view_layer.objects.active.bb2_pdbID not in selectedPDBidS:
                    t = copy.copy(bpy.context.view_layer.objects.active.bb2_pdbID)
                    selectedPDBidS.append(t)
            except Exception as E:
                str1 = str(E)  # Do not print...
                print("MLP on Surface ERROR 1" + str1)
            context.preferences.edit.use_global_undo = False
            for id in selectedPDBidS:
                bpy.ops.object.select_all(action="DESELECT")
                for o in bpy.data.objects:
                    o.select_set(False)
                for obj in bpy.context.scene.objects:
                    try:
                        if obj.bb2_pdbID == id:
                            obj.select_set(True)
                    except Exception as E:
                        str2 = str(E)
                        print("Error operator_mlp 2" + str(E))
                tID = copy.copy(id)
                mlp(tID, force=True, animation=False)
                panel.todoAndviewpoints()
            bpy.context.scene.BBViewFilter = "4"
            context.preferences.edit.use_global_undo = True
        except Exception as E:
            s = "Generate MLP visualization Failed.. MLP_PANEL 1: " + str(E)
            print(s)
            return {'CANCELLED'}
        else:
            return {'FINISHED'}


bpy.utils.register_class(bb2_OT_operator_mlp)


class bb2_OT_operator_mlp_render(bpy.types.Operator):
    bl_idname = "ops.bb2_operator_mlp_render"
    bl_label = "Render MLP to Surface"
    bl_description = "Visualize Molecular Lipophilicity Potential on surface"

    def invoke(self, context, event):
        try:
            context.preferences.edit.use_global_undo = False
            selectedPDBidS = []
            for b in bpy.context.scene.objects:
                if b.select_get():
                    try:
                        if (b.bb2_pdbID not in selectedPDBidS) and (b.bb2_objectType == "SURFACE"):
                            t = copy.copy(b.bb2_pdbID)
                            selectedPDBidS.append(t)
                    except Exception as E:
                        str1 = str(E)  # Do not print...
            context.preferences.edit.use_global_undo = False
            for id in selectedPDBidS:
                tID = copy.copy(id)
                mlpRender(tID)
                panel.todoAndviewpoints()
            context.scene.BBViewFilter = "4"
            context.preferences.edit.use_global_undo = True
        except Exception as E:
            s = "Generate MLP visualization Failed.. MLP_PANEL 2: " + str(E)
            print(s)
            return {'CANCELLED'}
        else:
            return {'FINISHED'}


bpy.utils.register_class(bb2_OT_operator_mlp_render)


# do MLP visualization
def mlp(tID, force, animation=False):

    namemlp = "MLP_Surface_" + NamePDBMLP(tID) + "_" + getNumFrameMLP()

    if ExistMLP(namemlp) == False:
        f = open(homePath + "tmp" + os.sep + "Object.txt", "w")
        f.write("frame " + str(bpy.data.scenes["Scene"].frame_current) + "\n")
        for obj in bpy.data.objects:
            if obj.bb2_pdbID == tID and obj.bb2_objectType == "PDBEMPTY":
                f.write("Path " + str(obj.bb2_pdbPath) + "\n")
                f.write("formula " + str(bpy.data.scenes["Scene"].BBMLPFormula) + "\n")
                f.write("spacing " + str(bpy.data.scenes["Scene"].BBMLPGridSpacing) + "\n")
                f.write("DeltaFrame " + str(bpy.data.scenes["Scene"].BBDeltaFrame) + "\n")
                f.write("Radio " + str(bpy.data.scenes["Scene"].BBMLPSolventRadius) + "\n")
            if obj.bb2_objectType == "ATOM" and obj.bb2_pdbID == tID:
                f.write("ATOM /" + obj.name + "/" + str(obj.location[0]) + "/" + str(obj.location[1]) + "/" + str(
                    obj.location[2]) + "\n")
                if str(obj.BBInfo.split()[2])[:1] == "H":
                    f.write("Hidrogeno" + "\n")

        f.close()


        bpy.ops.wm.save_as_mainfile(filepath=homePath + "tmp" + os.sep + "Obj.blend", compress=True, copy=True)

        Blender27Path = homePath + "data" + os.sep + "Blender" + os.sep + "blender.exe"
        #
        # Abrir script
        command = "%s --background --python %s" % (
            panel.quotedPath(Blender27Path), panel.quotedPath(homePath + "data" + os.sep + "Generar.py"))
        p = panel.launch(exeName=command)

        namelocation = ""
        bpy.ops.object.select_all(action="DESELECT")
        for o in bpy.data.objects:
            if o.bb2_pdbID == tID and o.bb2_pdbPath != '':
                namelocation = o.name
            o.select_set(False)
        bpy.context.view_layer.objects.active = None

        # Cargar la superficie
        Directory = homePath + "tmp" + os.sep + NamePDBMLP(
            tID) + os.sep + "mlpsurface.blend" + os.sep + "Object" + os.sep
        Path = os.sep + os.sep + "tmp" + os.sep + NamePDBMLP(
            tID) + os.sep + "mlpsurface.blend" + os.sep + "Object" + os.sep + namemlp
        objName = namemlp

        append_file_to_current_blend(Path, objName, Directory)
        bpy.data.objects[objName].bb2_pdbID = tID
        bpy.data.objects[objName].location = bpy.data.objects[namelocation].location


    else:
        bpy.ops.object.select_all(action="DESELECT")
        for o in bpy.data.objects:
            o.select_set(False)


def mlpRender(tID):
    print("MLP RENDER Start")
    scene = bpy.context.scene
    # Stop if no surface is found
    print(namemlp)
    scene.render.engine = 'BLENDER_EEVEE'


    for obj in bpy.data.objects:
        try:
            if (obj.bb2_pdbID == tID) and (obj.bb2_objectType == "SURFACE") and (obj.name.split("_")[0] != "SURFACE"):
                surfaceName = str(copy.copy(obj.name))

        except Exception as E:
            print("mlpRender(tID)" + str(E))
    ob = bpy.data.objects[surfaceName]


    print("Copy the needed files")
    uriSource = homePath + "data" + os.sep + "noise.png"
    uriDest = homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "noise.png"

    if opSystem == "linux":
        shutil.copy(uriSource, uriDest)
    elif opSystem == "darwin":
        shutil.copy(uriSource, uriDest)
    else:
        shutil.copy(r"\\?\\" + uriSource, r"\\?\\" + uriDest)

    uriSource = homePath + "data" + os.sep + "composite.blend"
    uriDest = homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "composite.blend"

    if opSystem == "linux":
        shutil.copy(uriSource, uriDest)
    elif opSystem == "darwin":
        shutil.copy(uriSource, uriDest)
    else:
        shutil.copy(r"\\?\\" + uriSource, r"\\?\\" + uriDest)

    # render out composite texture
    if blenderPath == "":
        bP = panel.quotedPath(str(os.environ['PWD']) + os.sep + "blender")
        command = "%s -b %s -f 1" % (panel.quotedPath(bP), panel.quotedPath(
            homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "composite.blend"))
    else:
        command = "%s -b %s -f 1" % (panel.quotedPath(blenderPath), panel.quotedPath(
            homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "composite.blend"))

    panel.launch(exeName=command)


    print("Copy the needed files")
    uriSource = homePath + "data" + os.sep + "MLP.blend"
    uriDest = homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "MLP.blend"

    if opSystem == "linux":
        shutil.copy(uriSource, uriDest)
    elif opSystem == "darwin":
        shutil.copy(uriSource, uriDest)
    else:
        shutil.copy(r"\\?\\" + uriSource, r"\\?\\" + uriDest)

    NameMaterial = "matMLP_" + NamePDBMLP(tID) + "_" + getNumFrameMLP()

    if os.path.exists(homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "0001_" + NamePDBMLP(tID) + "_" + getNumFrameMLP() + ".png"):
        os.remove(homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "0001_" + NamePDBMLP(tID) + "_" + getNumFrameMLP() + ".png")

    os.rename(homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "0001.png", homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "0001_" + NamePDBMLP(tID) + "_" + getNumFrameMLP() + ".png")
    try:
        mat = bpy.data.materials[NameMaterial]
        img_bump = bpy.data.images["0001_" + NamePDBMLP(tID) + "_" + getNumFrameMLP() + ".png"]
        bpy.data.images.remove(img_bump)
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.image.open(filepath=homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "0001.png", use_sequence_detection=True, relative_path=True)
        bpy.data.images["0001.png"].name = "0001_" + NamePDBMLP(tID) + "_" + getNumFrameMLP() + ".png"
        bpy.data.materials["matMLP_" + NamePDBMLP(tID) + "_" + getNumFrameMLP()].node_tree.nodes["Imagen"].image = bpy.data.images["0001_" + NamePDBMLP(tID) + "_" + getNumFrameMLP() + ".png"]
        #bpy.data.materials["matMLP_" + NamePDBMLP(tID)].node_tree.nodes["Imagen"].interpolation = 'Smart'
    except Exception as E:

        Directory = homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "MLP.blend" + os.sep + "Object" + os.sep
        Path = os.sep + os.sep + "tmp" + os.sep + NamePDBMLP(
            tID) + os.sep + "MLP.blend" + os.sep + "Object" + os.sep + "DirectLight"
        objName = "DirectLight"

        append_file_to_current_blend(Path, objName, Directory)


        Directory = homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "MLP.blend" + os.sep + "Material" + os.sep
        Path = os.sep + os.sep + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "MLP.blend" + os.sep + "Material" + os.sep + "matMLP"
        objName = "matMLP"

        append_file_to_current_blend(Path, objName, Directory)


        mat =  bpy.data.materials["matMLP"]
        mat.name = NameMaterial

        Directory = homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "MLP.blend" + os.sep + "Texture" + os.sep
        Path = os.sep + os.sep + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "MLP.blend" + os.sep + "Texture" + os.sep + "Surface"
        objName = "Surface"

        append_file_to_current_blend(Path, objName, Directory)

        bpy.data.textures["Surface"].name = "Surface_" + NamePDBMLP(tID)

        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.image.open(filepath=homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "0001_" + NamePDBMLP(tID) + "_" + getNumFrameMLP() + ".png", use_sequence_detection=True, relative_path=True)
        try:
            #img_bump = bpy.data.images["0001.png"]
            #img_bump.name = "0001_" + NamePDBMLP(tID) + "_" + getNumFrameMLP() + ".png"
            bpy.data.materials["matMLP_" + NamePDBMLP(tID) + "_" + getNumFrameMLP()].node_tree.nodes["Imagen"].image = bpy.data.images["0001_" + NamePDBMLP(tID) + "_" + getNumFrameMLP() + ".png"]
            #bpy.data.materials["matMLP_" + NamePDBMLP(tID)].node_tree.nodes["Imagen"].interpolation = 'Smart'

        except Exception as E:
            print("Error change name of the image" + str(E))

    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    try:
        ob.data.materials.pop(index=-1)
    except Exception as E:
        print("There is no material")
    ob.data.materials.append(mat)
    ob.data.materials.data.use_paint_mask_vertex = True

    if bpy.context.mode != 'EDIT_MESH':
        bpy.ops.object.editmode_toggle()
        bpy.ops.uv.smart_project(angle_limit=66, island_margin=0, user_area_weight=0)
        bpy.ops.object.editmode_toggle()

    for obj in bpy.context.scene.objects:
        if obj.BBInfo:
            #obj.hide_viewport = True
            obj.hide_render = True
    panel.ClearLigth(1)
    CleanShape()



# Wait until process finishes
def wait(process):
    while process.poll() is None:
        time.sleep(0.1)


def DeleteSurface():
    for surface in bpy.data.objects:
        surface.select_set(False)
        if surface.name.split("_")[0] == "SURFACE":
            surface.select_set(True)
    bpy.ops.object.delete()


def getNumFrameMLP():
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


def ExistMLP(nm):
    if nm in bpy.data.objects.keys():
        return True
    return False


def NamePDBMLP(tID):
    PDB = ""
    for o1 in bpy.context.scene.objects:
        try:
            if o1.bb2_pdbID == tID:
                if o1.bb2_objectType == "PDBEMPTY":
                    pE = copy.copy(o1.name)
                    PDB = str(pE)
        except Exception as E:
            str3 = str(E)  # Do not print...
            print("Error Name PDB " + str3)
    return PDB.split(".")[0]

def CleanShape():
    bpy.ops.object.select_all(action="DESELECT")
    if ("Shape_Sphere" in bpy.data.objects.keys()) or ("Shape_Cylinder" in bpy.data.objects.keys()):
        for obj in bpy.data.objects:
            obj.select_set(False)
            if obj.name[:12] == "Shape_Sphere":
                obj.select_set(True)
            if obj.name[:14] == "Shape_Cylinder":
                obj.select_set(True)
        bpy.ops.object.delete()

if __name__ == "__main__":
    print("MLP module created")
