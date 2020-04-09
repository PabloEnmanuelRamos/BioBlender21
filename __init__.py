import bpy
from bpy import *
from urllib.parse import urlencode
from urllib.request import *
from html.parser import *
from smtplib import *
from email.mime.text import MIMEText
import time, platform, os
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


# 2020-03-28
bl_info = {
    "name" : "BioBlender 2.1",
    "author" : "SciVis, IFC-CNR",
    "version" : (2,1),
    "blender" : (2,79,0),
    "location" : "Properties Window > Scene",
    "description" : "BioBlender 2.1",
    "warning" : "",
    "wiki_url" : "",
    "tracker_url" : "http://bioblender.eu/?page_id=665",
    "category" : "Add Mesh"
}


from .BioBlender2 import *
from .BB2_GUI_PDB_IMPORT import *
from .BB2_PANEL_VIEW import *
from .BB2_PHYSICS_SIM_PANEL import *
from .BB2_MLP_PANEL import *
from .BB2_PDB_OUTPUT_PANEL import *
from .BB2_OUTPUT_PANEL import *
from .BB2_NMA_PANEL import *
from .BB2_EP_PANEL import *




# ===== REGISTER = START ================================================
def register():
    bpy.utils.register_module(__name__)  # @UndefinedVariable

def unregister():
    bpy.utils.unregister_module(__name__)  # @UndefinedVariable

if __name__ == "__main__":
    register()
# ===== REGISTER = END ================================================