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
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)


bl_info = {
    "name" : "BioBlender Script",
    "author" : "SciVis, IFC-CNR",
    "version" : (2,0),
    "blender" : (2,6,8,0),
    "location" : "Properties Window > Scene",
    "description" : "BioBlender Script",
    "warning" : "",
    "wiki_url" : "",
    "tracker_url" : "http://bioblender.eu/?page_id=665",
    "category" : "Add Mesh"
}



# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================


from .Registrar import *


# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================



# ===== REGISTER = START ================================================
def register():
    bpy.utils.register_module(__name__)  # @UndefinedVariable

def unregister():
    bpy.utils.unregister_module(__name__)  # @UndefinedVariable

if __name__ == "__main__":
    register()
# ===== REGISTER = END ================================================