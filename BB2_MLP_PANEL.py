# coding= ascii
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
                        print("AtomicMLP ERROR 2" + str(E))
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
                        print("Error operator_mlp 2" + str(E))
                tID = copy.copy(id)
                mlp(tID, force=True)
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
def mlp(tID, force):
    global dxCacheM
    global method
    global dxData
    global dimension
    global origin
    global delta
    scene = bpy.context.scene
    formula = bpy.context.scene.BBMLPFormula
    spacing = bpy.context.scene.BBMLPGridSpacing
    namemlp = "MLP_Surface_" + NamePDBMLP(tID) + "_" + getNumFrameMLP()
    if not ExistMLP(namemlp):
        scene.render.engine = 'CYCLES'

        def getVar(rawID):
            try:
                val = dxCache[rawID]
            except:
                v = ob.data.vertices[rawID].co
                dimx = dimension[0]
                dimy = dimension[1]
                dimz = dimension[2]
                deltax = delta[0]
                deltay = delta[1]
                deltaz = delta[2]
                cellx = int((v[0] - origin[0]) / deltax)
                celly = int((v[1] - origin[1]) / deltay)
                cellz = int((v[2] - origin[2]) / deltaz)
                mmm = dxData[cellz + (celly * dimz) + (cellx * dimz * dimy)]
                pmm = dxData[cellz + (celly * dimz) + ((cellx + 1) * dimz * dimy)]
                mpm = dxData[cellz + ((celly + 1) * dimz) + (cellx * dimz * dimy)]
                mmp = dxData[cellz + 1 + (celly * dimz) + (cellx * dimz * dimy)]
                ppm = dxData[cellz + ((celly + 1) * dimz) + ((cellx + 1) * dimz * dimy)]
                mpp = dxData[cellz + 1 + ((celly + 1) * dimz) + (cellx * dimz * dimy)]
                pmp = dxData[cellz + 1 + (celly * dimz) + ((cellx + 1) * dimz * dimy)]
                ppp = dxData[cellz + 1 + ((celly + 1) * dimz) + ((cellx + 1) * dimz * dimy)]
                wxp = 1.0 - (fabs(v[0] - (origin[0] + (deltax * (cellx + 0.8))))) / deltax
                wxm = 1.0 - (fabs(v[0] - (origin[0] + (deltax * cellx)))) / deltax
                wyp = 1.0 - (fabs(v[1] - (origin[1] + (deltay * (celly + 0.8))))) / deltay
                wym = 1.0 - (fabs(v[1] - (origin[1] + (deltay * celly)))) / deltay
                wzp = 1.0 - (fabs(v[2] - (origin[2] + (deltaz * (cellz + 0.8))))) / deltaz
                wzm = 1.0 - (fabs(v[2] - (origin[2] + (deltaz * cellz)))) / deltaz
                onz_xmym = (wzp * mmp) + (wzm * mmm)
                onz_xpym = (wzp * pmp) + (wzm * pmm)
                onz_xmyp = (wzp * mpp) + (wzm * mpm)
                onz_xpyp = (wzp * ppp) + (wzm * ppm)
                onx_yp = (wxp * onz_xpyp) + (wxm * onz_xmyp)
                onx_ym = (wxp * onz_xpym) + (wxm * onz_xmym)
                val = (wyp * onx_yp) + (wym * onx_ym)
                dxCache[rawID] = val

            # map values
            if val >= 0.0:
                val = (val + 1.0) / 2.0
            else:
                val = (val + 3.0) / 6.0
            return [val, val, val]

        if force:
            panel.setup(setupPDBid=tID)
            # select formula for PyMLP script
            if formula == "0":
                method = "dubost"
            elif formula == "1":
                method = "testa"
            elif formula == "2":
                method = "fauchere"
            elif formula == "3":
                method = "brasseur"
            elif formula == "4":
                method = "buckingham"

            # Launch this in a separate process
            if opSystem == "linux":
                command = "chmod 755 %s" % (
                    panel.quotedPath(homePath + "bin" + os.sep + "pyMLP-1.0" + os.sep + "pyMLP.py"))
                command = panel.quotedPath(command)
                panel.launch(exeName=command)
            elif opSystem == "darwin":
                command = "chmod 755 %s" % (
                    panel.quotedPath(homePath + "bin" + os.sep + "pyMLP-1.0" + os.sep + "pyMLP.py"))
                command = panel.quotedPath(command)
                panel.launch(exeName=command)
            print("Running PyMLP")
            global pyPath
            if os.sys.platform == "linux":
                pyPath = "python"
                if os.path.exists("/usr/bin/python3"):
                    pyPath = "python3"
                elif os.path.exists("/usr/bin/python"):
                    pyPath = "python"
                elif os.path.exists("/usr/bin/python2"):
                    pyPath = "python2"
            if not pyPath:
                pyPath = "python"
            command = "%s %s -i %s -m %s -s %f -o %s -v" % (
                panel.quotedPath(pyPath),
                panel.quotedPath(homePath + "bin" + os.sep + "pyMLP-1.0" + os.sep + "pyMLP.py"),
                panel.quotedPath(homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "tmp.pdb"), method, spacing,
                panel.quotedPath(homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "tmp.dx"))

            p = panel.launch(exeName=command, asynct=True)

            print("PyMLP command succeded")
            panel.surface(sPid=tID, optName=namemlp)

            wait(p)

            # purge the all old data
            dxCache = {}
            dxData = []  # list[n] of Potential data
            dimension = []  # list[3] of dx grid store.dimension
            origin = []  # list[3] of dx grid store.origin
            delta = []  # list[3] of dx grid store.increment

            print("Loading MLP values into Blender")

            try:
                tmpPathO = homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "tmp.dx"
                with open(tmpPathO) as dx:
                    for line in dx:
                        # skip comments starting with #
                        if line[0] == "#":
                            continue
                        if not dimension:
                            # get the store.dimension and convert to integer
                            dim = line.split()[-3:]
                            dimension = [int(d) for d in dim]
                            size = dimension[0] * dimension[1] * dimension[2]
                            continue

                        if not origin:
                            # get the store.origin
                            org = line.split()[-3:]
                            origin = [float(o) for o in org]
                            continue

                        if not delta:
                            # get the increment delta
                            x = float(line.split()[-3:][0])
                            line = dx.readline()
                            y = float(line.split()[-3:][1])
                            line = dx.readline()
                            z = float(line.split()[-3:][2])
                            delta = [x, y, z]
                            # ignore more garbage lines
                            dx.readline()
                            dx.readline()
                            continue
                        # load as much data as we should, ignoring the rest of the file
                        if len(dxData) >= size:
                            break

                        # Load the data
                        # Convert dx data from str to float, then save to list
                        [dxData.append(float(coord)) for coord in line.split()]
            except Exception as E:
                print("An error occured in MLP while loading values into Blender; be careful; " + str(E))

        # quick and dirty update starts here
        if dxData:
            ob = bpy.data.objects[namemlp]
            ob.select_set(True)
            bpy.context.view_layer.objects.active = ob

            if not bpy.context.vertex_paint_object:
                bpy.ops.paint.vertex_paint_toggle()
            try:
                bpy.ops.object.editmode_toggle()
                bpy.ops.mesh.remove_doubles(threshold=0.0001, use_unselected=False)
                bpy.ops.object.editmode_toggle()
                bpy.ops.object.shade_smooth()
            except Exception as E:
                print("Error in MLP: remove doubles and shade smooth failed; " + str(E))

            try:
                ob.data.update()
            except Exception as E:
                print("Error in MLP: ob.data.update tessface failed; " + str(E))

            try:
                vColor0 = []
                vColor1 = []
                vColor2 = []
                ob.data.calc_loop_triangles()
                for f in ob.data.loop_triangles:
                    vColor0.extend(getVar(f.vertices[0]))
                    vColor1.extend(getVar(f.vertices[1]))
                    vColor2.extend(getVar(f.vertices[2]))
                for i in range(len(ob.data.vertex_colors[0].data)):
                    tmp = ((0.91 * vColor0[i]) + (0.98 * vColor1[i]) + (0.98 * vColor2[i])) / 3
                    ob.data.vertex_colors[0].data[i].color = (tmp, tmp, tmp, tmp)
            except Exception as E:
                print("Error in MLP: tessfaces vColor extend failed; " + str(E))

            try:
                me = ob.data
            except Exception as E:
                print("Error in MLP: me = ob.data failed; " + str(E))

            try:
                bpy.ops.paint.vertex_paint_toggle()
                me.use_paint_mask = False
                bpy.ops.paint.vertex_color_smooth()
                bpy.ops.paint.vertex_paint_toggle()
            except Exception as E:
                print("Error in MLP: vertex color smooth failed; " + str(E))

            try:
                # needed to make sure VBO is up to date
                ob.data.update()
            except Exception as E:
                print("Error in MLP: VBO ob.data.update failed; " + str(E))

        try:
            for obj in bpy.context.scene.objects:
                if obj.BBInfo:
                    # obj.hide_viewport = True
                    obj.hide_render = True
        except Exception as E:
            print("Error in MLP: obj.BBInfo")
        panel.ClearLigth(1)
        DeleteSurface()
        bpy.context.view_layer.objects.active = ob
        print("MLP function completed")

    else:
        bpy.ops.object.select_all(action="DESELECT")
        for o in bpy.data.objects:
            o.select_set(False)


def mlpRender(tID):
    print("MLP RENDER Start")
    scene = bpy.context.scene
    # Stop if no surface is found
    scene.render.engine = 'CYCLES'
    for obj in bpy.data.objects:
        try:
            if (obj.bb2_pdbID == tID) and (obj.bb2_objectType == "SURFACE") and (obj.name.split("_")[0] != "SURFACE"):
                surfaceName = str(copy.copy(obj.name))
        except Exception as E:
            print("mlpRender(tID)" + str(E))
    ob = bpy.data.objects[surfaceName]

    for o in bpy.data.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = None
    bpy.data.objects[surfaceName].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects[surfaceName]

    if not ob:
        raise Exception("No MLP Surface Found, select surface view first")

    # Stop if no dx data is loaded
    if not dxData:
        raise Exception("No MLP data is loaded.  Run MLP calculation first")

    # Vertex Color
    Directory = homePath + "data" + os.sep + "Vetex.blend" + os.sep + "Material" + os.sep
    Path = os.sep + os.sep + "data" + os.sep + "Vetex.blend" + os.sep + "Material" + os.sep + "matVetex"
    objName = "matVetex"

    append_file_to_current_blend(Path, objName, Directory)
    bpy.data.materials["matVetex"].name = "matMLP" + NamePDBMLP(tID) + "_" + getNumFrameMLP()
    mat = bpy.data.materials["matMLP" + NamePDBMLP(tID) + "_" + getNumFrameMLP()]
    ob.data.materials.append(mat)

    bpy.data.images["MLPBaked"].name = "MLPBaked" + NamePDBMLP(tID)
    image = bpy.data.images["MLPBaked" + NamePDBMLP(tID)]
    image.source = "GENERATED"
    image.generated_height = 2048
    image.generated_width = 2048

    if bpy.context.mode != "EDIT":
        bpy.ops.object.editmode_toggle()
        # ====
    for uv in ob.data.uv_layers[0].data:
        uv.image = image

    bpy.ops.uv.smart_project(angle_limit=66, island_margin=0, area_weight=0)

    for o in bpy.data.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = None
    bpy.context.view_layer.objects.active = bpy.data.objects[surfaceName]
    bpy.data.objects[surfaceName].select_set(True)
    bpy.ops.uv.smart_project(angle_limit=66, island_margin=0, area_weight=0)
    bpy.ops.uv.smart_project()
    bpy.context.space_data.context = 'RENDER'
    bpy.context.scene.cycles.bake_type = 'DIFFUSE'
    bpy.context.scene.render.bake.use_pass_direct = False
    bpy.context.scene.render.bake.use_pass_indirect = False
    bpy.context.scene.render.bake.margin = 16
    bpy.context.scene.render.bake.target = 'IMAGE_TEXTURES'
    print("===== BAKING... =====")
    bpy.ops.object.bake(type="DIFFUSE", filepath="", target='IMAGE_TEXTURES')
    print("=====          ... BAKED! =====")

    if opSystem == "linux":
        os.chdir(panel.quotedPath(homePath + "tmp" + os.sep + NamePDBMLP(
            tID) + os.sep))
    elif opSystem == "darwin":
        os.chdir(panel.quotedPath(homePath + "tmp" + os.sep + NamePDBMLP(
            tID) + os.sep))
    else:
        os.chdir(r"\\?\\" + homePath + "tmp" + os.sep + NamePDBMLP(
            tID) + os.sep)

    print("Image Save Render")
    image.save_render(homePath + "tmp" + os.sep + NamePDBMLP(
        tID) + os.sep + "MLPBaked.png")
    # copy the needed files
    print("Copy the needed files")
    uriSource = homePath + "data" + os.sep + "noise.png"
    uriDest = homePath + "tmp" + os.sep + NamePDBMLP(
        tID) + os.sep + "noise.png"

    if opSystem == "linux":
        shutil.copy(uriSource, uriDest)
    elif opSystem == "darwin":
        shutil.copy(uriSource, uriDest)
    else:
        shutil.copy(r"\\?\\" + uriSource, r"\\?\\" + uriDest)

    uriSource = homePath + "data" + os.sep + "composite.blend"
    uriDest = homePath + "tmp" + os.sep + NamePDBMLP(
        tID) + os.sep + "composite.blend"

    if opSystem == "linux":
        shutil.copy(uriSource, uriDest)
    elif opSystem == "darwin":
        shutil.copy(uriSource, uriDest)
    else:
        shutil.copy(r"\\?\\" + uriSource, r"\\?\\" + uriDest)

    # render out composite texture
    if blenderPath == "":
        bP = panel.quotedPath(str(os.environ['PWD']) + os.sep + "blender")
        command = "%s -b %s -f 1" % (panel.quotedPath(bP), panel.quotedPath(homePath + "tmp" + os.sep + NamePDBMLP(
            tID) + os.sep + "composite.blend"))
    else:
        command = "%s -b %s -f 1" % (panel.quotedPath(blenderPath), panel.quotedPath(homePath + "tmp" + os.sep + NamePDBMLP(
            tID) + os.sep + "composite.blend"))
    panel.launch(exeName=command)

    print("Copy the needed files")
    uriSource = homePath + "data" + os.sep + "MLPSurface.blend"
    uriDest = homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "MLPSurface.blend"

    if opSystem == "linux":
        shutil.copy(uriSource, uriDest)
    elif opSystem == "darwin":
        shutil.copy(uriSource, uriDest)
    else:
        shutil.copy(r"\\?\\" + uriSource, r"\\?\\" + uriDest)

    NameMaterial = "matMLP_" + NamePDBMLP(tID) + "_" + getNumFrameMLP()

    if os.path.exists(homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "0001_" + NamePDBMLP(
            tID) + "_" + getNumFrameMLP() + ".png"):
        os.remove(homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "0001_" + NamePDBMLP(
            tID) + "_" + getNumFrameMLP() + ".png")

    os.rename(homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "0001.png",
              homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "0001_" + NamePDBMLP(
                  tID) + "_" + getNumFrameMLP() + ".png")
    try:
        mat = bpy.data.materials[NameMaterial]
        img_bump = bpy.data.images["0001_" + NamePDBMLP(tID) + "_" + getNumFrameMLP() + ".png"]
        bpy.data.images["MLPBaked" + NamePDBMLP(tID)].name = "MLPBaked_" + NamePDBMLP(tID) + "_" + getNumFrameMLP()
        bpy.data.images.remove(img_bump)
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.image.open(filepath=homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "0001.png", use_sequence_detection=True, relative_path=True)
        bpy.data.images["0001.png"].name = "0001_" + NamePDBMLP(tID) + "_" + getNumFrameMLP() + ".png"
        bpy.data.materials["matMLP_" + NamePDBMLP(tID) + "_" + getNumFrameMLP()].node_tree.nodes["Imagen"].image = bpy.data.images["0001_" + NamePDBMLP(tID) + "_" + getNumFrameMLP() + ".png"]
        bpy.data.materials["matMLP_" + NamePDBMLP(tID) + "_" + getNumFrameMLP()].node_tree.nodes["Image Texture"].image = bpy.data.images["MLPBaked_" + NamePDBMLP(tID) + "_" + getNumFrameMLP()]
    except Exception as E:
        bpy.context.view_layer.objects.active = None
        bpy.ops.object.select_all(action="DESELECT")
        for o in bpy.data.objects:
            o.select_set(False)

        Directory = homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "MLPSurface.blend" + os.sep + "Object" + os.sep
        Path = os.sep + os.sep + "tmp" + os.sep + NamePDBMLP(
            tID) + os.sep + "MLPSurface.blend" + os.sep + "Object" + os.sep + "DirectLight"
        objName = "DirectLight"

        append_file_to_current_blend(Path, objName, Directory)

        Directory = homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "MLPSurface.blend" + os.sep + "Material" + os.sep
        Path = os.sep + os.sep + "tmp" + os.sep + NamePDBMLP(
            tID) + os.sep + "MLPSurface.blend" + os.sep + "Material" + os.sep + "matMLP"
        objName = "matMLP"

        append_file_to_current_blend(Path, objName, Directory)

        mat = bpy.data.materials["matMLP"]
        mat.name = NameMaterial

        Directory = homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "MLPSurface.blend" + os.sep + "Texture" + os.sep
        Path = os.sep + os.sep + "tmp" + os.sep + NamePDBMLP(
            tID) + os.sep + "MLPSurface.blend" + os.sep + "Texture" + os.sep + "Surface"
        objName = "Surface"

        append_file_to_current_blend(Path, objName, Directory)

        bpy.data.textures["Surface"].name = "Surface_" + NamePDBMLP(tID) + "_" + getNumFrameMLP()

        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.image.open(filepath=homePath + "tmp" + os.sep + NamePDBMLP(tID) + os.sep + "0001_" + NamePDBMLP(
            tID) + "_" + getNumFrameMLP() + ".png", use_sequence_detection=True, relative_path=True)

        bpy.data.images["MLPBaked" + NamePDBMLP(tID)].name = "MLPBaked_" + NamePDBMLP(tID) + "_" + getNumFrameMLP()
        try:
            bpy.data.materials["matMLP_" + NamePDBMLP(tID) + "_" + getNumFrameMLP()].node_tree.nodes["Imagen"].image = bpy.data.images["0001_" + NamePDBMLP(tID) + "_" + getNumFrameMLP() + ".png"]
            bpy.data.materials["matMLP_" + NamePDBMLP(tID) + "_" + getNumFrameMLP()].node_tree.nodes["Image Texture"].image = bpy.data.images["MLPBaked_" + NamePDBMLP(tID) + "_" + getNumFrameMLP()]
        except Exception as E:
            print("Error change name of the image" + str(E))
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    try:
        ob.data.materials.pop(index=-1)
    except Exception as E:
        print("There is no material " + str(E))
    ob.data.materials.append(mat)
    ob.data.materials.data.use_paint_mask_vertex = True

    if bpy.context.mode != 'EDIT_MESH':
        bpy.ops.object.editmode_toggle()
        bpy.ops.uv.smart_project(angle_limit=66, island_margin=0, user_area_weight=0)
        bpy.ops.object.editmode_toggle()

    for obj in bpy.context.scene.objects:
        if obj.BBInfo:
            # obj.hide_viewport = True
            obj.hide_render = True
    scene.render.engine = 'BLENDER_EEVEE'
    panel.ClearLigth(0)  # Before 1
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
    print("MLP")
