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
# ===== Fixes =================
'''

2021 / juL / 03
- [added 'append_file_to_current_blend`] use instead of link_append
- fixed reference to modelList -> tmpModel
- added pymol.cmd to pyMolPathSearch
'''

bpy.types.Object.BBInfo = bpy.props.StringProperty()

# ===== HELPERS ===============


def append_file_to_current_blend(Path, objName, Directory):
    """
    for the time being this will permit older versions of Blender to use the append feature
    """

    print('appending file')
    wm = bpy.ops.wm
    # if hasattr(wm, 'link_append'):
    if 'link_append' in dir(wm):
        wm.link_append(filepath=Path, filename=objName, directory=Directory, link=False)
    else:
        wm.append(filepath=Path, filename=objName, directory=Directory)


# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================


bpy.types.Object.BBInfo = bpy.props.StringProperty()  # From BioBlender1
bpy.types.Object.bb2_pdbID = bpy.props.StringProperty()  # bb2_pdbID        --- Numerical, incremental
bpy.types.Object.bb2_objectType = bpy.props.StringProperty()  # bb2_objectType   --- ATOM, PDBEMPTY, CHAINEMPTY,
# SURFACE
bpy.types.Object.bb2_subID = bpy.props.StringProperty()  # bb2_subID --- e.g.: Chain ID
bpy.types.Object.bb2_pdbPath = bpy.props.StringProperty()  # bb2_pdbPath --- just for Empties; e.g.: in Setup function
bpy.types.Object.bb2_outputOptions = bpy.props.EnumProperty(name="bb2_outputoptions", default="1",
                                                            items=[("0", "Main", ""), ("1", "+Side", ""),
                                                                   ("2", "+Hyd", ""), ("3", "Surface", ""),
                                                                   ("4", "MLP Main", ""), ("5", "MLP +Side", ""),
                                                                   ("6", "MLP +Hyd", ""), ("7", "MLP Surface", "")])

# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================


# OS detection
os.environ["opSystem"] = ""
if os.sys.platform == "linux":
    os.environ["opSystem"] = "linux"
elif os.sys.platform == "darwin":
    os.environ["opSystem"] = "darwin"
else:
    os.environ["opSystem"] = "win"

# Home Path
os.environ["BBHome"] = os.path.dirname(__file__) + os.sep
os.environ["BBHome_BIN"] = os.environ["BBHome"] + "bin" + os.sep
os.environ["BBHome_TEMP"] = os.environ["BBHome"] + "tmp" + os.sep
os.environ["BBHome_BIN_PDBPQR"] = os.environ["BBHome_BIN"] + "pdb2pqr-1.6" + os.sep
os.environ["BBHome_DATA"] = os.environ["BBHome"] + "data" + os.sep
os.environ["BBHome_FETCHED"] = os.environ["BBHome"] + "fetched" + os.sep
os.environ["BBHome_BIN_SCIVIS"] = os.environ["BBHome_BIN"] + "scivis" + os.sep
os.environ["BBHome_BIN_APBS"] = os.environ["BBHome_BIN"] + "apbs-1.2.1" + os.sep
os.environ["BBHome_BIN_NMA"] = os.environ["BBHome_BIN"] + "nma" + os.sep + "nma.py"
os.environ["BBHome_BIN_PyMLP"] = os.environ["BBHome_BIN"] + "pyMLP-1.0" + os.sep


# Blender Path
path_blender = str(sys.executable).split(os.sep)
path_blend = ""
for i in range(len(path_blender) - 4):
    path_blend += path_blender[i] + os.sep

os.environ["blenderPath"] = ""
if os.sys.platform == "linux" or os.sys.platform == "darwin":
    if os.path.exists(path_blend + "blender"):
        os.environ["blenderPath"] = path_blend + "blender"
    else:
        os.environ["blenderPath"] = "blender"
else:
    os.environ["blenderPath"] = path_blend + "blender.exe"


# Python Path
if (str(os.environ["opSystem"]) == "linux") or (str(os.environ["opSystem"]) == "darwin"):
    os.environ["pyPath"] = "python"
    if os.path.exists("/usr/bin/python3.10"):
        os.environ["pyPath"] = "python3.10"
    if os.path.exists("/usr/bin/python3.9"):
        os.environ["pyPath"] = "python3.9"
    elif os.path.exists("/usr/bin/python3.8"):
        os.environ["pyPath"] = "python3.8"
    elif os.path.exists("/usr/bin/python3.7"):
        os.environ["pyPath"] = "python3.7"
    elif os.path.exists("/usr/bin/python3"):
        os.environ["pyPath"] = "python3"
    elif os.path.exists("/usr/bin/python"):
        os.environ["pyPath"] = "python"
    elif os.path.exists("/usr/bin/python2"):
        os.environ["pyPath"] = "python2"
else:
    os.environ["pyPath"] = ""
    pyPathSearch = ["%programfiles%\\Python310\\python.exe", "%programfiles%\\Python39\\python.exe", "%programfiles%\\Python38\\python.exe", "%programfiles%\\Python37\\python.exe", "%programfiles%\\Python35\\python.exe", "%systemdrive%\\Python310\\python.exe", "%systemdrive%\\Python39\\python.exe", "%systemdrive%\\Python38\\python.exe", "%systemdrive%\\Python37\\python.exe", "%systemdrive%\\Python35\\python.exe", "/usr/bin/python"]


# Detecting PyMol path
os.environ["pyMolPath"] = ""
pyMolPathSearch = [
    "%systemdrive%\\Python39\\Scripts\\pymol.cmd",
    "%systemdrive%\\Python38\\Scripts\\pymol.cmd",
    "%systemdrive%\\Python37\\Scripts\\pymol.cmd",
    "%programfiles%\\PyMOL\\PyMOL\\PymolWin.exe",
    "%programfiles%\\DeLano Scientific\\PyMOL Eval\\PymolWin.exe",
    "%programfiles%\\DeLano Scientific\\PyMOL\\PymolWin.exe",
    "%programfiles(x86)%\\PyMOL\\PyMOL\\PymolWin.exe",
    "%programfiles(x86)%\\DeLano Scientific\\PyMOL Eval\\PymolWin.exe",
    "%programfiles(x86)%\\DeLano Scientific\\PyMOL\\PymolWin.exe", 
    "C:\\ProgramData\\PyMOL\\PymolWin.exe",
    "C:\\ProgramData\\DeLano Scientific\\PyMOL Eval\\PymolWin.exe",
    "C:\\ProgramData\\DeLano Scientific\\PyMOL\\PymolWin.exe"
]

if (str(os.environ["opSystem"]) == "linux") or (str(os.environ["opSystem"]) == "darwin"):
    os.environ["pyMolPath"] = "pymol"
else:
    from winreg import ExpandEnvironmentStrings

    # auto detect pymol path
    if not os.environ["pyMolPath"]:
        for i in pyMolPathSearch:
            if os.path.exists(ExpandEnvironmentStrings(i)):
                os.environ["pyMolPath"] = ExpandEnvironmentStrings(i)
                break
    # auto detect python path
    if not os.environ["pyPath"]:
        for i in pyPathSearch:
            if os.path.exists(ExpandEnvironmentStrings(i)):
                os.environ["pyPath"] = ExpandEnvironmentStrings(i)
                break


if not os.environ["pyMolPath"]:
    os.environ["pyMolPath"] = "pymol"

if not os.environ["pyPath"]:
    os.environ["pyPath"] = "python"
# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================


bootstrap = -1  # A way to avoid infamous RestricContext error on boot

# Generic BB2 "Global" variables
curFrame = 1
filePath = ""
activeTag = ""  # the active/selected model
projectLastFrame = 1  # Used in multi-pdb context to calculate offset Frame for GE Simulation

# PDB-MODELS-related variables (no chains-related variables)
pdbID = 0
pdbIDmodelsDictionary = {}  # Key: pdb_ID;  value: a dictionary containing all the models of the current (ID) PDB

# CHAINS-related variables
chainCount = 0  # PDB import preview: chains number in PDB
importChainID = []  # PDB import preview: chains names in PDB
importChainOrderList = []  # PDB import preview: chains to be imported
mainChainCacheDict = {}  # a cache to that contains only mainchain atoms for the various PDBid (key)
mainChainCache_NucleicDict = {}
mainChainCache_Nucleic_FilteredDict = {}
chainCacheDict = {}  # a cache to that contains all non-H atoms for the various PDBid (key)
chainCache_NucleicDict = {}
ChainModels = {}  # cache to contain model of chains and atoms belonging to chains

# EP-related variables
epOBJ = []  # holds a list of object generated by the EP visualization
curveCount = 0  # a counter for EP curves
dxData = []  # list[n] of Potential data
dimension = []  # list[3] of dx grid dimension
origin = []  # list[3] of dx grid origin
dxCache = {}  # cache to speed up vertexColor mapping
maxCurveSet = 4

# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================


# Define common atom name as variables to avoid RSI from typing quotes
C = "C"
N = "N"
O = "O"
S = "S"
H = "H"
CA = "CA"
P = "P"
FE = "FE"
MG = "MG"
ZN = "ZN"
CU = "CU"
NA = "NA"
K = "K"
CL = "CL"
MN = "MN"
F = "F"
NucleicAtoms = ["P", "O2P", "OP2", "O1P", "OP1", "O5'", "C5'", "C4'", "C3'", "O4'", "C1'", "C2'", "O3'", "O2'"]
NucleicAtoms_Filtered = ["P", "O5'", "C5'", "C4'", "C3'", "O3'"]

# Define atom color [R,G,B]
color = {C: [0.1, 0.1, 0.1, 1.0], CA: [0.4, 1.0, 0.14, 1.0], N: [0.24, 0.41, 0.7, 1.0], O: [0.46, 0.1, 0.1, 1.0], S: [1.0, 0.75, 0.17, 1.0],
         P: [1.0, 0.37, 0.05, 1.0], FE: [1.0, 0.5, 0.0, 1.0], MG: [0.64, 1.0, 0.05, 1.0], ZN: [0.32, 0.42, 1, 1.0], CU: [1.0, 0.67, 0.0, 1.0],
         NA: [0.8, 0.48, 1.0, 1.0], K: [0.72, 0.29, 1.0, 1.0], CL: [0.1, 1.0, 0.6, 1.0], MN: [0.67, 0.6, 1.0, 1.0], H: [0.9, 0.9, 0.9, 1.0],
         F: [0.27, 0.8, 0.21, 1.0]}

dic_lipo_materials = {}

# Define animoacids structure
molecules_structure = {'ALA': ['CB', 'C', 'CA', 'O', 'N', 'H', 'HA', 'HB1', 'HB2', 'HB3', 'H1', 'H2', 'H3', 'OXT'],
                       'ARG': ['C', 'CA', 'CB', 'CD', 'CG', 'CZ', 'N', 'NE', 'NH1', 'NH2', 'O', 'H', 'HA', 'HB2', 'HB3',
                               'HG2', 'HG3', 'HD2', 'HD3', 'HE', 'HH11', 'HH12', 'HH21', 'HH22', '1HH1', '2HH1', '1HH2',
                               '2HH2', 'H1', 'H2', 'H3', 'OXT'],
                       'ASN': ['C', 'CA', 'CB', 'CG', 'N', 'ND2', 'O', 'OD1', 'H', 'HA', 'HB2', 'HB3', 'HD21', 'HD22',
                               '1HD2', '2HD2', 'H1', 'H2', 'H3', 'OXT'],
                       'ASP': ['C', 'CA', 'CB', 'CG', 'N', 'O', 'OD1', 'OD2', 'H', 'HA', 'HB2', 'HB3', 'H1', 'H2', 'H3',
                               'OXT'],
                       'CYS': ['C', 'CA', 'CB', 'N', 'O', 'SG', 'H', 'HA', 'HB2', 'HB3', 'H1', 'H2', 'H3', 'OXT'],
                       'GLN': ['C', 'CA', 'CB', 'CD', 'CG', 'N', 'NE2', 'O', 'OE1', 'H', 'HA', 'HB2', 'HB3', 'HG2',
                               'HG3', 'HE21', 'HE22', '1HE2', '2HE2', 'H1', 'H2', 'H3', 'OXT'],
                       'GLU': ['C', 'CA', 'CB', 'CD', 'CG', 'N', 'O', 'OE1', 'OE2', 'H', 'HA', 'HB2', 'HB3', 'HG2',
                               'HG3', 'H1', 'H2', 'H3', 'OXT'],
                       'GLY': ['C', 'CA', 'O', 'N', 'H', 'HA', 'HA2', 'HA3', 'H1', 'H2', 'H3', 'OXT'],
                       'HIS': ['C', 'CA', 'CB', 'CD2', 'CE1', 'CG', 'N', 'ND1', 'NE2', 'O', 'H', 'HA', 'HB2', 'HB3',
                               'HD1', 'HD2', 'HE1', 'H1', 'H2', 'H3', 'OXT'],
                       'ILE': ['C', 'CA', 'CB', 'CD', 'CD1', 'CG1', 'CG2', 'N', 'O', 'H', 'HA', 'HB', 'HG12', 'HG13',
                               'HG21', 'HG22', 'HG23', 'HD11', 'HD12', 'HD13', '2HG1', '3HG1', '1HG2', '2HG2', '3HG2',
                               '1HD1', '2HD1', '3HD1', 'H1', 'H2', 'H3', 'OXT'],
                       'LEU': ['C', 'CA', 'CB', 'CD1', 'CD2', 'CG', 'N', 'O', 'H', 'HA', 'HB2', 'HB3', 'HG', 'HD11',
                               'HD12', 'HD13', 'HD21', 'HD22', 'HD23', '1HD1', '2HD1', '3HD1', '1HD1', '2HD2', '3HD2',
                               'H1', 'H2', 'H3', 'OXT'],
                       'LYS': ['C', 'CA', 'CB', 'CD', 'CE', 'CG', 'N', 'NZ', 'O', 'H', 'HA', 'HB2', 'HB3', 'HG2', 'HG3',
                               'HD2', 'HD3', 'HE2', 'HE3', 'HZ1', 'HZ2', 'HZ3', 'H1', 'H2', 'H3', 'OXT'],
                       'MET': ['C', 'CA', 'CB', 'CE', 'CG', 'N', 'O', 'SD', 'H', 'HA', 'HB2', 'HB3', 'HG2', 'HG3',
                               'HE1', 'HE2', 'HE3', 'H1', 'H2', 'H3', 'OXT'],
                       'PHE': ['C', 'CA', 'CB', 'CD1', 'CD2', 'CE1', 'CE2', 'CG', 'CZ', 'N', 'O', 'H', 'HA', 'HB2',
                               'HB3', 'HD1', 'HD2', 'HE1', 'HE2', 'HZ', 'H1', 'H2', 'H3', 'OXT'],
                       'PRO': ['C', 'CA', 'CB', 'CD', 'CG', 'N', 'O', 'HA', 'HB2', 'HB3', 'HG2', 'HG3', 'HD2', 'HD3',
                               'H1', 'H2', 'H3', 'OXT'],
                       'SER': ['C', 'CA', 'CB', 'N', 'O', 'OG', 'H', 'HA', 'HB2', 'HB3', 'HG', 'H1', 'H2', 'H3', 'OXT'],
                       'THR': ['C', 'CA', 'CB', 'CG2', 'N', 'O', 'OG1', 'H', 'HA', 'HB', 'HG1', 'HG21', 'HG22', 'HG23',
                               '1HG2', '2HG2', '3HG2', 'H1', 'H2', 'H3', 'OXT'],
                       'TRP': ['C', 'CA', 'CB', 'CD1', 'CD2', 'CE2', 'CE3', 'CG', 'CH2', 'CZ2', 'CZ3', 'N', 'NE1', 'O',
                               'H', 'HA', 'HB2', 'HB3', 'HE1', 'HD1', 'HE3', 'HZ2', 'HZ3', 'HH2', 'H1', 'H2', 'H3',
                               'OXT'],
                       'TYR': ['C', 'CA', 'CB', 'CD1', 'CD2', 'CE1', 'CE2', 'CG', 'CZ', 'N', 'O', 'OH', 'H', 'HA',
                               'HB2', 'HB3', 'HD1', 'HD2', 'HE1', 'HE2', 'HH', 'H1', 'H2', 'H3', 'OXT'],
                       'VAL': ['C', 'CA', 'CB', 'CG1', 'CG2', 'N', 'O', 'H', 'HA', 'HB', 'HG11', 'HG12', 'HG13', 'HG21',
                               'HG22', 'HG23', '1HG1', '2HG1', '3HG1', '1HG2', '2HG2', '3HG2', 'H1', 'H2', 'H3', 'OXT'],
                       'CA': ['CA'],
                       'NAG': ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'O1', 'O2', 'O3', 'O4', 'O5', 'O6', 'O7',
                               'N2', 'H2', 'HN2'],
                       'NDG': ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'O1L', 'O3', 'O4', 'O', 'O6', 'O7',
                               'N2'], 'BMA': ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'O1', 'O2', 'O3', 'O4', 'O5', 'O6'],
                       'MAN': ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'O1', 'O2', 'O3', 'O4', 'O5', 'O6'],
                       'GAL': ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'O1', 'O2', 'O3', 'O4', 'O5', 'O6'],
                       'NAN': ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'O1A', 'O1B', 'O2',
                               'O4', 'O6', 'O7', 'O8', 'O9', 'O10', 'N5', 'NH5'],
                       'DG': ['P', 'O1P', 'O2P', "O5'", "C5'", "C4'", "O4'", "C1'", "C2'", "C3'", "O3'", 'N9', 'C8',
                              'N7', 'C5', 'C6', 'O6', 'N1', 'C2', 'N2', 'N3', 'C4'],
                       'DA': ['P', 'O1P', 'O2P', "O5'", "C5'", "C4'", "O4'", "C1'", "C2'", "C3'", "O3'", 'N9', 'C8',
                              'N7', 'C5', 'C6', 'N6', 'N1', 'C2', 'N2', 'N3', 'C4'],
                       'DC': ['P', 'O1P', 'O2P', "O5'", "C5'", "C4'", "O4'", "C1'", "C2'", "C3'", "O3'", 'N1', 'C2',
                              'O2', 'N3', 'C4', 'N4', 'C5', 'C6'],
                       'DT': ['P', 'O1P', 'O2P', "O5'", "C5'", "C4'", "O4'", "C1'", "C2'", "C3'", "O3'", 'N1', 'C2',
                              'O2', 'N3', 'C4', 'O4', 'C5', 'C6', 'C7'],
                       'G': ['P', 'O1P', 'O2P', "O5'", "C5'", "C4'", "O4'", "C1'", "C2'", "O2'", "C3'", "O3'", 'N9',
                             'C8', 'N7', 'C5', 'C6', 'O6', 'N1', 'C2', 'N2', 'N3', 'C4'],
                       'A': ['P', 'O1P', 'O2P', "O5'", "C5'", "C4'", "O4'", "C1'", "C2'", "O2'", "C3'", "O3'", 'N9',
                             'C8', 'N7', 'C5', 'C6', 'N6', 'N1', 'C2', 'N2', 'N3', 'C4'],
                       'C': ['P', 'O1P', 'O2P', "O5'", "C5'", "C4'", "O4'", "C1'", "C2'", "O2'", "C3'", "O3'", 'N1',
                             'C2', 'O2', 'N3', 'C4', 'N4', 'C5', 'C6'],
                       'U': ['P', 'O1P', 'O2P', "O5'", "C5'", "C4'", "O4'", "C1'", "C2'", "O2'", "C3'", "O3'", 'N1',
                             'C2', 'O2', 'N3', 'C4', 'O4', 'C5', 'C6']}

values_fi = {
    'ALA': {'CB': '0.62', 'C': '-0.61', 'CA': '0.02', 'O': '-0.58', 'N': '-0.49', 'H': '-0.5', 'HA': '-0.25',
            'HB1': '0.0', 'HB2': '0.0', 'HB3': '0.0', 'H1': '-0.5', 'H2': '-0.5', 'H3': '-0.5', 'OXT': '0.49'},
    'ARG': {'C': '-0.61', 'CA': '0.02', 'CB': '0.45', 'CD': '0.45', 'CG': '0.45', 'CZ': '-0.61', 'N': '-0.49',
            'NE': '-0.49', 'NH1': '-0.14', 'NH2': '-0.69', 'O': '-0.58', 'H': '-0.5', 'HA': '-0.25', 'HB2': '0.0',
            'HB3': '0.0', 'HG2': '0.0', 'HG3': '0.0', 'HD2': '-0.25', 'HD3': '-0.25', 'HE': '-0.5', 'HH11': '-0.5',
            'HH12': '-0.5', 'HH21': '-0.5', 'HH22': '-0.5', '1HH1': '-0.5', '2HH1': '-0.5', '1HH2': '-0.5',
            '2HH2': '-0.5', 'H1': '-0.5', 'H2': '-0.5', 'H3': '-0.5', 'OXT': '0.49'},
    'ASN': {'C': '-0.61', 'CA': '0.02', 'CB': '0.02', 'CG': '-0.61', 'N': '-0.49', 'ND2': '-0.14', 'O': '-0.58',
            'OD1': '-0.58', 'H': '-0.5', 'HA': '-0.25', 'HB2': '0.0', 'HB3': '0.0', 'HD21': '-0.5', 'HD22': '-0.5',
            '1HD2': '-0.5', '2HD2': '-0.5', 'H1': '-0.5', 'H2': '-0.5', 'H3': '-0.5', 'OXT': '0.49'},
    'ASP': {'C': '-0.61', 'CA': '0.02', 'CB': '0.45', 'CG': '-0.61', 'N': '-0.49', 'O': '-0.58', 'OD1': '-0.58',
            'OD2': '0.49', 'H': '-0.5', 'HA': '-0.25', 'HB2': '0.0', 'HB3': '0.0', 'H1': '-0.5', 'H2': '-0.5',
            'H3': '-0.5', 'OXT': '0.49'},
    'CYS': {'C': '-0.61', 'CA': '0.02', 'CB': '0.45', 'N': '-0.49', 'O': '-0.58', 'SG': '0.29', 'H': '-0.5',
            'HA': '-0.25', 'HB2': '0.0', 'HB3': '0.0', 'H1': '-0.5', 'H2': '-0.5', 'H3': '-0.5', 'OXT': '0.49'},
    'GLN': {'C': '-0.61', 'CA': '0.02', 'CB': '0.45', 'CD': '-0.54', 'CG': '0.45', 'N': '-0.49', 'NE2': '-0.14',
            'O': '-0.58', 'OE1': '-0.58', 'H': '-0.5', 'HA': '-0.25', 'HB2': '0.0', 'HB3': '0.0', 'HG2': '0.0',
            'HG3': '0.0', 'HE21': '-0.5', 'HE22': '-0.5', '1HE2': '-0.5', '2HE2': '-0.5', 'H1': '-0.5', 'H2': '-0.5',
            'H3': '-0.5', 'OXT': '0.49'},
    'GLU': {'C': '-0.61', 'CA': '0.02', 'CB': '0.45', 'CD': '-0.54', 'CG': '0.45', 'N': '-0.49', 'O': '-0.58',
            'OE1': '-0.58', 'OE2': '0.49', 'H': '-0.5', 'HA': '-0.25', 'HB2': '0.0', 'HB3': '0.0', 'HG2': '0.0',
            'HG3': '0.0', 'H1': '-0.5', 'H2': '-0.5', 'H3': '-0.5', 'OXT': '0.49'},
    'GLY': {'C': '-0.61', 'CA': '0.45', 'O': '-0.58', 'N': '-0.57', 'H': '-0.5', 'HA': '-0.25', 'HA2': '0.0',
            'HA3': '0.0', 'H1': '-0.5', 'H2': '-0.5', 'H3': '-0.5', 'OXT': '0.49'},
    'HIS': {'C': '-0.61', 'CA': '0.02', 'CB': '0.45', 'CD2': '0.31', 'CE1': '0.31', 'CG': '0.1', 'N': '-0.49',
            'ND1': '0.08', 'NE2': '-1.14', 'O': '-0.58', 'H': '-0.5', 'HA': '-0.25', 'HB2': '0.0', 'HB3': '0.0',
            'HD1': '-0.5', 'HD2': '-0.25', 'HE1': '-0.25', 'H1': '-0.5', 'H2': '-0.5', 'H3': '-0.5', 'OXT': '0.49'},
    'ILE': {'C': '-0.61', 'CA': '0.02', 'CB': '0.02', 'CD': '0.63', 'CD1': '0.63', 'CG1': '0.45', 'CG2': '0.63',
            'N': '-0.49', 'O': '-0.58', 'H': '-0.5', 'HA': '-0.25', 'HB': '0.0', 'HG12': '0.0', 'HG13': '0.0',
            'HG21': '0.0', 'HG22': '0.0', 'HG23': '0.0', 'HD11': '0.0', 'HD12': '0.0', 'HD13': '0.0', '2HG1': '0.0',
            '3HG1': '0.0', '1HG2': '0.0', '2HG2': '0.0', '3HG2': '0.0', '1HD1': '0.0', '2HD1': '0.0', '3HD1': '0.0',
            'H1': '-0.5', 'H2': '-0.5', 'H3': '-0.5', 'OXT': '0.49'},
    'LEU': {'C': '-0.61', 'CA': '0.02', 'CB': '0.45', 'CD1': '0.63', 'CD2': '0.63', 'CG': '0.02', 'N': '-0.49',
            'O': '-0.58', 'H': '-0.5', 'HA': '-0.25', 'HB2': '0.0', 'HB3': '0.0', 'HG': '0.0', 'HD11': '0.0',
            'HD12': '0.0', 'HD13': '0.0', 'HD21': '0.0', 'HD22': '0.0', 'HD23': '0.0', '1HD1': '0.0', '2HD1': '0.0',
            '3HD1': '0.0', '1HD2': '0.0', '2HD2': '0.0', '3HD2': '0.0', 'H1': '-0.5', 'H2': '-0.5', 'H3': '-0.5',
            'OXT': '0.49'},
    'LYS': {'C': '-0.61', 'CA': '0.02', 'CB': '0.45', 'CD': '0.45', 'CE': '0.45', 'CG': '0.45', 'N': '-0.49',
            'NZ': '-1.07', 'O': '-0.58', 'H': '-0.5', 'HA': '-0.25', 'HB2': '0.0', 'HB3': '0.0', 'HG2': '0.0',
            'HG3': '0.0', 'HD2': '0.0', 'HD3': '0.0', 'HE2': '-0.25', 'HE3': '-0.25', 'HZ1': '-0.5', 'HZ2': '-0.5',
            'HZ3': '-0.5', 'H1': '-0.5', 'H2': '-0.5', 'H3': '-0.5', 'OXT': '0.49'},
    'MET': {'C': '-0.61', 'CA': '0.02', 'CB': '0.45', 'CE': '0.63', 'CG': '0.45', 'N': '-0.49', 'O': '-0.58',
            'SD': '-0.30', 'H': '-0.5', 'HA': '-0.25', 'HB2': '0.0', 'HB3': '0.0', 'HG2': '0.0', 'HG3': '0.0',
            'HE1': '0.0', 'HE2': '0.0', 'HE3': '-0.5', 'H1': '-0.5', 'H2': '-0.5', 'H3': '-0.5', 'OXT': '0.49'},
    'PHE': {'C': '-0.61', 'CA': '0.02', 'CB': '0.45', 'CD1': '0.31', 'CD2': '0.31', 'CE1': '0.31', 'CE2': '0.31',
            'CG': '0.1', 'CZ': '0.31', 'N': '-0.49', 'O': '-0.58', 'H': '-0.5', 'HA': '-0.25', 'HB2': '0.0',
            'HB3': '0.0', 'HD1': '0.0', 'HD2': '0.0', 'HE1': '0.0', 'HE2': '0.0', 'HZ': '0.0', 'H1': '-0.5',
            'H2': '-0.5', 'H3': '-0.5', 'OXT': '0.49'},
    'PRO': {'C': '-0.61', 'CA': '0.02', 'CB': '0.45', 'CD': '0.45', 'CG': '0.45', 'N': '-0.92', 'O': '-0.58',
            'HA': '-0.25', 'HB2': '0.0', 'HB3': '0.0', 'HG2': '0.0', 'HG3': '0.0', 'HD2': '-0.25', 'HD3': '-0.25',
            'H1': '-0.5', 'H2': '-0.5', 'H3': '-0.5', 'OXT': '0.49'},
    'SER': {'C': '-0.61', 'CA': '0.02', 'CB': '0.45', 'N': '-0.49', 'O': '-0.58', 'OG': '-0.99', 'H': '-0.5',
            'HA': '-0.25', 'HB2': '0.0', 'HB3': '0.0', 'HG': '0.0', 'H1': '-0.5', 'H2': '-0.5', 'H3': '-0.5',
            'OXT': '0.49'},
    'THR': {'C': '-0.61', 'CA': '0.02', 'CB': '0.02', 'CG2': '0.62', 'N': '-0.49', 'O': '-0.58', 'OG1': '-0.92',
            'H': '-0.5', 'HA': '-0.25', 'HB': '0.0', 'HG1': '0.0', 'HG21': '0.0', 'HG22': '0.0', 'HG23': '0.0',
            '1HG2': '0.0', '2HG2': '0.0', '3HG2': '0.0', 'H1': '-0.5', 'H2': '-0.5', 'H3': '-0.5', 'OXT': '0.49'},
    'TRP': {'C': '-0.61', 'CA': '0.02', 'CB': '0.45', 'CD1': '0.31', 'CD2': '0.25', 'CE2': '0.25', 'CE3': '0.31',
            'CG': '0.1', 'CH2': '0.31', 'CZ2': '0.31', 'CZ3': '0.31', 'N': '-0.49', 'NE1': '0.08', 'O': '-0.58',
            'H': '-0.5', 'HA': '-0.25', 'HB2': '0.0', 'HB3': '0.0', 'HE1': '-0.5', 'HD1': '-0.25', 'HE3': '0.0',
            'HZ2': '0.0', 'HZ3': '0.0', 'HH2': '0.0', 'H1': '-0.5', 'H2': '-0.5', 'H3': '-0.5', 'OXT': '0.49'},
    'TYR': {'C': '-0.61', 'CA': '0.02', 'CB': '0.45', 'CD1': '0.31', 'CD2': '0.31', 'CE1': '0.31', 'CE2': '0.31',
            'CG': '0.1', 'CZ': '0.1', 'N': '-0.49', 'O': '-0.58', 'OH': '-0.17', 'H': '-0.5', 'HA': '-0.25',
            'HB2': '0.0', 'HB3': '0.0', 'HD1': '0.0', 'HD2': '0.0', 'HE1': '0.0', 'HE2': '0.0', 'HH': '0.0',
            'H1': '-0.5', 'H2': '-0.5', 'H3': '-0.5', 'OXT': '0.49'},
    'VAL': {'C': '-0.61', 'CA': '0.02', 'CB': '0.02', 'CG1': '0.62', 'CG2': '0.62', 'N': '-0.49', 'O': '-0.58',
            'H': '-0.5', 'HA': '-0.25', 'HB': '0.0', 'HG11': '0.0', 'HG12': '0.0', 'HG13': '0.0', 'HG21': '0.0',
            'HG22': '0.0', 'HG23': '0.0', '1HG1': '0.0', '2HG1': '0.0', '3HG1': '0.0', '1HG2': '0.0', '2HG2': '0.0',
            '3HG2': '0.0', 'H1': '-0.5', 'H2': '-0.5', 'H3': '-0.5', 'OXT': '0.49'},
    'CA': {'CA': '-1.0'},
    'ZN': {'ZN': '-1.0'},
    'NAG': {'C1': '0.02', 'C2': '0.02', 'C3': '0.02', 'C4': '0.02', 'C5': '0.02', 'C6': '0.31', 'C7': '-0.61',
            'C8': '0.62', 'O1': '-0.92', 'O2': '-0.92', 'O3': '-0.92', 'O4': '-0.92', 'O5': '-1.14', 'O6': '-0.99',
            'O7': '-0.58', 'N2': '-0.49', 'H2': '-0.25', 'HN2': '-0.5'},
    'NDG': {'C1': '0.02', 'C2': '0.02', 'C3': '0.02', 'C4': '0.02', 'C5': '0.02', 'C6': '0.031', 'C7': '-0.61',
            'C8': '0.62', 'O1L': '-0.92', 'O3': '-0.92', 'O4': '-0.92', 'O': '-1.14', 'O6': '-0.99', 'O7': '-0.58',
            'N2': '-0.29'},
    'BMA': {'C1': '0.02', 'C2': '0.02', 'C3': '0.02', 'C4': '0.02', 'C5': '0.02', 'C6': '0.31', 'O1': '-0.92',
            'O2': '-0.92', 'O3': '-0.92', 'O4': '-0.92', 'O5': '-1.14', 'O6': '-0.58'},
    'MAN': {'C1': '0.02', 'C2': '0.02', 'C3': '0.02', 'C4': '0.02', 'C5': '0.02', 'C6': '0.31', 'O1': '-0.92',
            'O2': '-0.92', 'O3': '-0.92', 'O4': '-0.92', 'O5': '-1.14', 'O6': '-0.58'},
    'GAL': {'C1': '0.02', 'C2': '0.02', 'C3': '0.02', 'C4': '0.02', 'C5': '0.02', 'C6': '0.31', 'O1': '-0.92',
            'O2': '-0.92', 'O3': '-0.92', 'O4': '-0.92', 'O5': '-1.14', 'O6': '-0.58'},
    'NAN': {'C1': '-0.61', 'C2': '0.02', 'C3': '0.62', 'C4': '0.02', 'C5': '0.02', 'C6': '0.02', 'C7': '0.02',
            'C8': '0.02', 'C9': '0.31', 'C10': '-0.61', 'C11': '0.62', 'O1A': '-0.21', 'O1B': '-0.46', 'O2': '-0.92',
            'O4': '-0.92', 'O6': '-1.14', 'O7': '-0.92', 'O8': '-0.92', 'O9': '-0.7', 'O10': '-0.22', 'N5': '-0.49',
            'NH5': '-0.5'},
    'DG': {'P': '-0.94', 'O1P': '-0.7', 'O2P': '-0.22', 'OP1': '-0.7', 'OP2': '-0.22', "O5'": '-0.5', "C5'": '0.45',
           "C4'": '0.02', "O4'": '-1.14', "C1'": '0.02', "C2'": '0.45', "C3'": '0.02', "O3'": '-0.92', 'N9': '-1.66',
           'C8': '0.31', 'N7': '-0.55', 'C5': '0.25', 'C6': '0.1', 'O6': '-0.58', 'N1': '-0.49', 'C2': '0.1',
           'N2': '-0.6', 'N3': '-0.07', 'C4': '-0.25'},
    'DA': {'P': '-0.94', 'O1P': '-0.7', 'O2P': '-0.22', 'OP1': '-0.7', 'OP2': '-0.22', "O5'": '-0.5', "C5'": '0.45',
           "C4'": '0.02', "O4'": '-1.14', "C1'": '0.02', "C2'": '0.45', "C3'": '0.02', "O3'": '-0.92', 'N9': '-1.66',
           'C8': '0.31', 'N7': '-0.55', 'C5': '0.25', 'C6': '0.1', 'N6': '-0.6', 'N1': '-0.49', 'C2': '0.31',
           'N2': '-0.6', 'N3': '-0.07', 'C4': '-0.25'},
    'DC': {'P': '-0.94', 'O1P': '-0.7', 'O2P': '-0.22', 'OP1': '-0.7', 'OP2': '-0.22', "O5'": '-0.5', "C5'": '0.45',
           "C4'": '0.02', "O4'": '-1.14', "C1'": '0.02', "C2'": '0.45', "C3'": '0.02', "O3'": '-0.92', 'N1': '-1.66',
           'C2': '0.1', 'O2': '-0.58', 'N3': '-0.29', 'C4': '0.1', 'N4': '-0.6', 'C5': '0.31', 'C6': '0.31'},
    'DT': {'P': '-0.94', 'O1P': '-0.7', 'O2P': '-0.22', 'OP1': '-0.7', 'OP2': '-0.22', "O5'": '-0.5', "C5'": '0.45',
           "C4'": '0.02', "O4'": '-1.14', "C1'": '0.02', "C2'": '0.45', "C3'": '0.02', "O3'": '-0.92', 'N1': '-1.66',
           'C2': '0.1', 'O2': '-0.58', 'N3': '0.16', 'C4': '0.25', 'O4': '-0.58', 'C5': '0.1', 'C6': '0.31',
           'C7': '0.45'},
    'G': {'P': '-0.94', 'O1P': '-0.7', 'O2P': '-0.22', 'OP1': '-0.7', 'OP2': '-0.22', "O5'": '-0.5', "C5'": '0.45',
          "C4'": '0.02', "O4'": '-1.14', "C1'": '0.02', "C2'": '0.02', "O2'": '-0.92', "C3'": '0.02', "O3'": '-0.92',
          'N9': '-1.66', 'C8': '0.31', 'N7': '-0.55', 'C5': '0.25', 'C6': '0.1', 'O6': '-0.58', 'N1': '-0.49',
          'C2': '0.1', 'N2': '-0.6', 'N3': '-0.07', 'C4': '-0.25'},
    'A': {'P': '-0.94', 'O1P': '-0.7', 'O2P': '-0.22', 'OP1': '-0.7', 'OP2': '-0.22', "O5'": '-0.5', "C5'": '0.45',
          "C4'": '0.02', "O4'": '-1.14', "C1'": '0.02', "C2'": '0.02', "O2'": '-0.92', "C3'": '0.02', "O3'": '-0.92',
          'N9': '-1.66', 'C8': '0.31', 'N7': '-0.55', 'C5': '0.25', 'C6': '0.1', 'N6': '-0.6', 'N1': '-0.49',
          'C2': '0.31', 'N2': '-0.6', 'N3': '-0.07', 'C4': '-0.25'},
    'C': {'P': '-0.94', 'O1P': '-0.7', 'O2P': '-0.22', 'OP1': '-0.7', 'OP2': '-0.22', "O5'": '-0.5', "C5'": '0.45',
          "C4'": '0.02', "O4'": '-1.14', "C1'": '0.02', "C2'": '0.02', "O2'": '-0.92', "C3'": '0.02', "O3'": '-0.92',
          'N1': '-1.66', 'C2': '0.1', 'O2': '-0.58', 'N3': '-0.29', 'C4': '0.1', 'N4': '-0.6', 'C5': '0.31',
          'C6': '0.31'},
    'U': {'P': '-0.94', 'O1P': '-0.7', 'O2P': '-0.22', 'OP1': '-0.7', 'OP2': '-0.22', "O5'": '-0.5', "C5'": '0.45',
          "C4'": '0.02', "O4'": '-1.14', "C1'": '0.02', "C2'": '0.02', "O2'": '-0.92', "C3'": '0.02', "O3'": '-0.92',
          'N1': '-1.66', 'C2': '0.1', 'O2': '-0.58', 'N3': '0.16', 'C4': '0.25', 'O4': '-0.58', 'C5': '0.1',
          'C6': '0.31'},
    'GLC': {'C1': '0.02', 'C2': '0.02', 'C3': '0.02', 'C4': '0.02', 'C5': '0.02', 'C6': '0.31', 'O7': '-0.92',
            'O8': '-0.92', 'O9': '-0.92', 'O10': '-0.92', 'O11': '-1.14', 'O12': '-0.58'}
}

# Define atom scales [visual Van der Waals scale, collision radius scale]
scale_vdw = {C: [1.35, 0.6], CA: [1.59, 0.6], N: [1.23, 0.6], O: [1.2, 0.6], S: [1.43, 0.6], P: [1.43, 0.6],
             FE: [1.59, 0.6], MG: [1.37, 0.6], ZN: [1.1, 0.6], CU: [1.1, 0.6], NA: [1.8, 0.6], K: [2.18, 0.6],
             CL: [1.37, 0.6], MN: [1.59, 0.6], H: [0.95, 0.3], F: [1.16, 0.6]}

# Define atom scales [visual covalent scale, collision radius scale]
scale_cov = {C: [1.1, 0.6], CA: [0.99, 0.6], N: [1.07, 0.6], O: [1.04, 0.6], S: [1.46, 0.6], P: [1.51, 0.6],
             FE: [0.64, 0.6], MG: [0.65, 0.6], ZN: [0.74, 0.6], CU: [0.72, 0.6], NA: [0.95, 0.6], K: [1.33, 0.6],
             CL: [1.81, 0.6], MN: [0.46, 0.6], H: [0.53, 0.3], F: [1.36, 0.6]}

# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================

# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================

print("BlenderPath: " + str(os.environ["blenderPath"]))
print("PythonPath: " + str(os.environ["pyPath"]))
print("PyMolPath: " + str(os.environ["pyMolPath"]))

if __name__ == "__main__":
    print("BioBlender2 module created")
