# -*- coding: utf-8 -*-
import bpy
from bpy import *
import bpy_types
from urllib.parse import urlencode
from urllib.request import *
from html.parser import *
from smtplib import *
from email.mime.text import MIMEText
import time
import platform
import os
import codecs
import bpy.path
from bpy.path import abspath
import base64
import mathutils
from mathutils import *
from math import *
import pickle
import shutil
import subprocess
import sys

from .BB2_GUI_PDB_IMPORT import *
from .BioBlender2 import *
from .BB2_PANEL_VIEW import *
from .BB2_MLP_PANEL import *
from .BB2_EP_PANEL import *
# from .BB2_PDB_OUTPUT_PANEL import *
from .BB2_NMA_PANEL import *
from .BB2_OUTPUT_PANEL import *


# 2021-07-03
bl_info = {
    "name": "BioBlender 2.1",
    "author": "SciVis, IFC-CNR",
    "version": (2, 1),
    "blender": (2, 93, 0),
    "location": "Properties > Scene",
    "description": "BioBlender 2.1",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "http://www.scivis.it/community/main-forum/bioblender-for-blender-2-93/",
    "category": "Mesh"
}


# ===== CLASS  IMPORT PDB==========================================================================================

importReady = False


class BB2_PT_GUI_PDB_IMPORT(bpy.types.Panel):
    bl_idname = "SCENE_PT_BB2_GUI_PDB_IMPORT"
    bl_label = "BioBlender 2 PDB import"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    bpy.types.Scene.BBDeltaFrame = bpy.props.IntProperty(attr="BBDeltaFrame", name="Keyframe Interval",
                                                         description="The number of in-between frames between each model for animation",
                                                         default=100, min=1, max=500, soft_min=5, soft_max=200)
    bpy.types.Scene.BBImportPath = bpy.props.StringProperty(attr="BBImportPath", name="", description="Select PBD file", default="",
                                                            subtype="FILE_PATH")
    bpy.types.Scene.BBModelRemark = bpy.props.StringProperty(attr="BBModelRemark", name="",
                                                             description="Model name tag for multiple imports",
                                                             default="protein0")
    bpy.types.Scene.BBImportFeedback = bpy.props.StringProperty(attr="BBImportFeedback", name="", description="Import Feedback",
                                                                default="")
    bpy.types.Scene.BBImportChain = bpy.props.StringProperty(attr="BBImportChain", name="", description="Import Chain",
                                                             default="")
    bpy.types.Scene.BBImportChainOrder = bpy.props.StringProperty(attr="BBImportChainOrder", name="",
                                                                  description="List of chains to be imported",
                                                                  default="")
    bpy.types.Scene.BBImportOrder = bpy.props.StringProperty(attr="BBImportOrder", name="",
                                                             description="List of models to be imported", default="")
    bpy.types.Scene.BBImportHydrogen = bpy.props.BoolProperty(attr="BBImportHydrogen", name="Import Hydrogen",
                                                              description="Import hydrogen atoms (Slower)",
                                                              default=False)

    # ================
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        split = layout.split()
        split.prop(scene, "BBImportPath")
        if len(bpy.context.scene.BBImportPath) >= 4:
            split.operator("ops.bb2_operator_make_preview")
        row = layout.row()
        row.prop(scene, "BBModelRemark")
        row = layout.row()
        if importReady and len(bpy.context.scene.BBImportPath) >= 4:
            # left column
            split = layout.split()
            col = split.column()
            col.prop(scene, "BBImportOrder", text="")
            # right column
            col = split.column()
            col.prop(scene, "BBDeltaFrame")
            # next row
            row = layout.row()
            row.prop(scene, "BBImportFeedback", emboss=False)
            row = layout.row()
            row.prop(scene, "BBImportChain", emboss=False)
            row = layout.row()
            row.prop(scene, "BBImportChainOrder")
            row = layout.row()
            row.prop(scene, "BBImportHydrogen")
            row = layout.row()
            row.scale_y = 2
            row.operator("ops.bb2_operator_import")
        else:
            row = layout.row()
            row.scale_y = 2
            row.active = False
            row.operator("ops.bb2_operator_import", text="Not Ready to Import", icon="X")


class bb2_OT_operator_make_preview(bpy.types.Operator):
    bl_idname = "ops.bb2_operator_make_preview"
    bl_label = "Make Preview"
    bl_description = "Make Preview"

    def invoke(self, context, event):
        try:
            global importReady
            importReady = False
            if len(bpy.context.scene.BBImportPath) >= 4:
                if bootstrap == -1:
                    bootstrapping()
                bpy.context.scene.BBImportFeedback = ""
                bpy.context.scene.BBImportChain = ""
                bpy.context.scene.BBImportOrder = ""
                bpy.context.scene.BBImportChainOrder = ""
                importReady = importPreview(retrieved=False)
                print("Import Ready: " + str(importReady))
        except Exception as E:
            s = "Import Failed 1: " + str(E)
            print(s)
            return {'CANCELLED'}
        else:
            return {'FINISHED'}


bpy.utils.register_class(bb2_OT_operator_make_preview)


# ===== CLASS  PANEL VIEW ============================================================================================

class BB2_PT_PANEL_VIEW(bpy.types.Panel):
    bl_label = "BioBlender2 View"
    bl_idname = "SCENE_PT_BB2_PANEL_VIEW"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    bpy.types.Scene.BBMLPSolventRadius = bpy.props.FloatProperty(attr="BBMLPSolventRadius", name="Solvent Radius",
                                                                 description="Solvent Radius used for Surface Generation",
                                                                 default=1.4, min=0.2, max=5, soft_min=0.4, soft_max=4)
    bpy.types.Scene.BBViewFilter = bpy.props.EnumProperty(attr="BBViewFilter", name="",
                                                          description="Select a view mode",
                                                          items=(("1", "Main Chain", ""),
                                                                 ("2", "+ Side Chain", ""),
                                                                 ("3", "+ Hydrogen", ""),
                                                                 ("4", "Surface", "")),
                                                          default="3")

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        r = layout.column(align=False)
        if bpy.context.view_layer.objects.active:
            if bpy.context.view_layer.objects.active.bb2_pdbPath:
                r.label(text="Currently Selected Model: " + str(bpy.context.view_layer.objects.active.name))
            elif bpy.context.view_layer.objects.active.BBInfo:
                r.label(text="Currently Selected Model: " + str(bpy.context.view_layer.objects.active.name))
                r.alignment = 'LEFT'
                r.prop(bpy.context.view_layer.objects.active, "BBInfo", icon="MATERIAL", emboss=False)
            else:
                r.label(text="No model selected")
        split = layout.split()
        r = split.row()
        r.prop(scene, "BBViewFilter", expand=False)
        if bpy.context.scene.BBViewFilter == "4":
            split = split.row(align=True)
            split.prop(scene, "BBMLPSolventRadius")
        r = layout.row()
        r.operator("ops.bb2_view_panel_update", text="APPLY")

    @classmethod
    def poll(cls, context):
        global tag
        global currentActiveObj
        global oldActiveObj
        try:
            if bpy.context.view_layer.objects.active.name is not None:
                # do a view update when the selected/active obj changes
                if bpy.context.view_layer.objects.active.name != oldActiveObj:
                    # get the ModelRemark of the active model
                    if bpy.context.view_layer.objects.active.name:
                        activeModelRemark = bpy.context.view_layer.objects.active.name.split("#")[0]
                        # load previous sessions from cache
                        # if not modelContainer:
                        # sessionLoad()
                        # print("Sessionload")
                        currentActiveObj = activeModelRemark
                    oldActiveObj = bpy.context.view_layer.objects.active.name
        except Exception as E:
            s = "Context Poll Failed: " + str(E)  # VEEEEEERY ANNOYING...
        return context


# ===== CLASS GAME ==================================================================================================
geList = []

'''
class BB2_PT_PHYSICS_SIM_PANEL(bpy.types.Panel):
    bl_label = "BioBlender2 Game Engine Sim"
    bl_idname = "SCENE_PT_BB2_PHYSICS_SIM_PANEL"
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
        split = r.split()
        try:
            for m in geList:
                split.label(str(m))
                split.prop(bpy.context.scene.objects[str(m)].game, "physics_type")
                r = layout.row()
                split = r.split()
        except Exception as E:
            print("An error occured in SIM_PANEL.draw while drawing geList")
        r = layout.row()
        split = r.split(align = True)
        split.prop(scene, "BBRecordAnimation")
        split.prop(scene, "BBDeltaPhysicRadius")
        r = layout.row()
        r.operator("ops.bb2_operator_interactive")


'''
# ===== CLASS  MLP ===================================================================================================


class BB2_PT_MLP_PANEL(bpy.types.Panel):
    bl_label = "BioBlender2 MLP Visualization"
    bl_idname = "SCENE_PT_BB2_MLP_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    bpy.types.Scene.BBAtomic = bpy.props.EnumProperty(attr="BBAtomic", name="BBAtomic",
                                                      description="Atomic or Surface MLP",
                                                      items=(("0", "Atomic", ""), ("1", "Surface", "")), default="0")
    bpy.types.Scene.BBMLPFormula = bpy.props.EnumProperty(attr="BBMLPFormula", name="Formula",
                                                          description="Select a formula for MLP calculation", items=(("0", "Dubost", ""), ("1", "Testa", ""), ("2", "Fauchere", ""), ("3", "Brasseur", ""), ("4", "Buckingham", "")), default="1")
    bpy.types.Scene.BBMLPGridSpacing = bpy.props.FloatProperty(attr="BBMLPGridSpacing", name="Grid Spacing",
                                                               description="MLP Calculation step size (Smaller is better, but slower)",
                                                               default=1, min=0.01, max=20, soft_min=1.4, soft_max=10)
    bpy.types.Scene.BBMLPSolventRadius = bpy.props.FloatProperty(attr="BBMLPSolventRadius", name="Solvent Radius",
                                                                 description="Solvent Radius used for Surface Generation",
                                                                 default=1.4, min=0.2, max=5, soft_min=0.4, soft_max=4)
    bpy.types.Scene.BBAtomicMLP = bpy.props.BoolProperty(attr="BBAtomicMLP", name="Atomic MLP", default=False)

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        r = layout.column(align=False)
        if bpy.context.view_layer.objects.active:
            if bpy.context.view_layer.objects.active.bb2_pdbPath or bpy.context.view_layer.objects.active.BBInfo:
                r.label(text="Currently Selected Model: " + str(bpy.context.view_layer.objects.active.name))
            elif bpy.context.view_layer.objects.active.bb2_objectType == 'SURFACE' and bpy.context.view_layer.objects.active.name[:3] == 'MLP':
                r.label(text="Currently Selected Surface: " + str(bpy.context.view_layer.objects.active.name[12:]))
            else:
                r.label(text="No model or surface selected")
        r = layout.row()
        r.prop(scene, "BBAtomic", expand=True)
        r = layout.row()
        if bpy.context.scene.BBAtomic == "0":
            r.label(text="Calculate Atomic MLP")
            r = layout.row()
            r.scale_y = 2
            r.operator("ops.bb2_operator_atomic_mlp")
        else:
            split = layout.split()
            c = split.column()
            c.prop(scene, "BBMLPFormula")
            c.prop(scene, "BBMLPGridSpacing")
            c.prop(scene, "BBMLPSolventRadius")
            r = split.row()
            r.scale_y = 2
            if bpy.context.view_layer.objects.active is not None:
                if bpy.context.view_layer.objects.active.bb2_pdbPath and bpy.context.view_layer.objects.active.bb2_objectType == "PDBEMPTY":
                    r.operator("ops.bb2_operator_mlp")
                else:
                    r.active = False
                    r.operator("ops.bb2_operator_mlp", icon="X")
            else:
                r.active = False
                r.operator("ops.bb2_operator_mlp", icon="X")
            split = layout.split()
            r = split.column(align=True)
            r = split.column()
            r.scale_y = 2
            if bpy.context.view_layer.objects.active is not None:
                if bpy.context.view_layer.objects.active.bb2_objectType == 'SURFACE' and bpy.context.view_layer.objects.active.name[:3] == 'MLP':
                    r.operator("ops.bb2_operator_mlp_render")
                else:
                    r.active = False
                    r.operator("ops.bb2_operator_mlp_render", icon="X")
            else:
                r.active = False
                r.operator("ops.bb2_operator_mlp_render", icon="X")


# ===== CLASS  EP =====================================================================================================


class BB2_PT_EP_PANEL(bpy.types.Panel):
    bl_label = "BioBlender2 EP Visualization"
    bl_idname = "SCENE_PT_BB2_EP_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    bpy.types.Scene.BBForceField = bpy.props.EnumProperty(attr="BBForceField", name="ForceField",
                                                          description="Select a forcefield type for EP calculation",
                                                          items=(("0", "amber", ""),
                                                                 ("1", "charmm", ""),
                                                                 ("2", "parse", ""),
                                                                 ("3", "tyl06", ""),
                                                                 ("4", "peoepb", ""),
                                                                 ("5", "swanson", "")),
                                                          default="0")
    bpy.types.Scene.BBEPIonConc = bpy.props.FloatProperty(attr="BBEPIonConc", name="Ion concentration",
                                                          description="Ion concentration of the solvent", default=0.15,
                                                          min=0.01, max=1, soft_min=0.01, soft_max=1)
    bpy.types.Scene.BBEPGridStep = bpy.props.FloatProperty(attr="BBEPGridStep", name="Grid Spacing",
                                                           description="EP Calculation step size (Smaller is better, but slower)",
                                                           default=1, min=0.01, max=10, soft_min=0.5, soft_max=5)
    bpy.types.Scene.BBEPMinPot = bpy.props.FloatProperty(attr="BBEPMinPot", name="Minimum Potential",
                                                         description="Minimum Potential on the surface from which start the calculation of the field lines",
                                                         default=0.0, min=0.0, max=10000, soft_min=0, soft_max=1000)
    bpy.types.Scene.BBEPNumOfLine = bpy.props.FloatProperty(attr="BBEPNumOfLine", name="n EP Lines*eV/Å² ",
                                                            description="Concentration of lines", default=0.05,
                                                            min=0.01, max=0.5, soft_min=0.01, soft_max=0.1, precision=3,
                                                            step=0.01)
    bpy.types.Scene.BBEPParticleDensity = bpy.props.FloatProperty(attr="BBEPParticleDensity", name="Particle Density",
                                                                  description="Particle Density", default=1, min=0.1,
                                                                  max=10.0, soft_min=0.1, soft_max=5.0)

    def draw(self, context):
        scene = bpy.context.scene
        layout = self.layout
        split = layout.split()
        c = split.column()
        c.prop(scene, "BBForceField")
        c = c.column(align=True)
        c.label(text="Options:")
        c.prop(scene, "BBEPIonConc")
        c.prop(scene, "BBEPGridStep")
        c.prop(scene, "BBEPMinPot")
        c.prop(scene, "BBEPNumOfLine")
        c.prop(scene, "BBEPParticleDensity")
        c = split.column()
        c.scale_y = 2
        c.operator("ops.bb2_operator_ep")
        c.operator("ops.bb2_operator_ep_clear")


# ===== CLASS  PDB EXPORT  ============================================================================================

"""
class BB2_PT_PDB_OUTPUT_PANEL(bpy.types.Panel):
    bl_label = "BioBlender2 PDB Output"
    bl_idname = "SCENE_PT_BB2_PDB_OUTPUT_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    bpy.types.Scene.BBPDBExportStep = bpy.props.IntProperty(attr="BBPDBExportStep", name="PDB Export Step",
                                                            description="PDB Export step", default=1, min=1, max=100,
                                                            soft_min=1, soft_max=50)

    def draw(self, context):
        scene = bpy.context.scene
        layout = self.layout
        r = layout.row()
        r.prop(bpy.context.scene.render, "filepath", text="")
        r = layout.row()
        r.prop(bpy.context.scene, "frame_start")
        r = layout.row()
        r.prop(bpy.context.scene, "frame_end")
        r = layout.row()
        r.prop(bpy.context.scene, "BBPDBExportStep")
        r = layout.row()
        r.operator("ops.bb2_operator_export_pdb")
        r = layout.row()
        num = ((bpy.context.scene.frame_end - bpy.context.scene.frame_start) / bpy.context.scene.BBPDBExportStep) + 1
        r.label(text = "A total of %d frames will be exported." % num)

"""
# ===== CLASS EXPORT MOVIE ===========================================================================================

class BB2_PT_OUTPUT_PANEL(bpy.types.Panel):
    bl_label = "BioBlender2 Movie Output"
    bl_idname = "SCENE_PT_BB2_OUTPUT_PANEL"
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
                    r.label(text=str(ob.name))
                    r = layout.row()
                    r.prop(ob, "bb2_outputOptions")
                    r = layout.row()
            except Exception as E:
                print("An error occured in BB2_OUTPUT_PANEL: " + str(E))  # Do nothing...
        r.prop(bpy.context.scene.render, "stamp_note_text", text="Notes")
        r = layout.row()
        r.prop(bpy.context.scene.render, "use_stamp", text="Information Overlay")
        r = layout.row()
        r.prop(bpy.context.scene.render, "filepath", text="")
        r = layout.row()
        r.prop(bpy.context.scene, "frame_start")
        r = layout.row()
        r.prop(bpy.context.scene, "frame_end")
        r = layout.row()
        r.prop(bpy.context.scene, "BBExportStep")
        r = layout.row()
        stp = bpy.context.scene.BBExportStep
        num = ((bpy.context.scene.frame_end - bpy.context.scene.frame_start) / stp) + 1
        r.label(text="A total of %d frames will be exported." % (((bpy.context.scene.frame_end - bpy.context.scene.frame_start) / bpy.context.scene.BBExportStep) + 1))
        r = layout.row()
        if bpy.context.scene.camera is not None:
            r.operator("ops.bb2_operator_anim")
        else:
            r.active = False
            r.operator("ops.bb2_operator_anim", text='Export Movie (No Camera)', icon='X')


# ===== CLASS NMA ====================================================================================================

class BB2_PT_NMA_PANEL(bpy.types.Panel):
    bl_label = "BioBlender2 NMA Visualization"
    bl_idname = "SCENE_PT_BB2_NMA_PANEL"
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
        c.label(text="Options:")
        c.prop(scene, "BBNMANbModel")
        c.prop(scene, "BBNMARMSD")
        c.prop(scene, "BBNMACutoff")
        c.prop(scene, "BBNMAGamma")
        c = c.column(align=True)
        c = split.column()
        c.scale_y = 2
        c.operator("ops.bb2_operator_nma")


# ===== REGISTER = START ============================================================================
classes = (
    BB2_PT_GUI_PDB_IMPORT,
    BB2_PT_PANEL_VIEW,
    # BB2_PT_PHYSICS_SIM_PANEL,
    BB2_PT_MLP_PANEL,
    BB2_PT_EP_PANEL,
    # BB2_PT_PDB_OUTPUT_PANEL,
    BB2_PT_OUTPUT_PANEL,
    BB2_PT_NMA_PANEL,
)

register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()
