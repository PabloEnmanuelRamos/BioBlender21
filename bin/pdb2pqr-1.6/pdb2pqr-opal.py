#!@WHICHPYTHON@
"""
    Driver for interfacing pdb2pqr web form with OPAL SOAP job submission.
    
"""
from io import StringIO

__date__ = "5 April 2010"
__author__ = "Wes Goodman, Yong Huang"
__version__ = "1.6"

from .src.server import *
from .src.hydrogens import *
from .src.aconf import *
from .src.utilities import *

from .AppService_client import AppServiceLocator, launchJobRequest
from .AppService_types import ns0
import cgi
import cgitb


def printheader(pagetitle, jobid=None):
    """
        Function to print html headers
  """
    if jobid:
        print("Location: querystatus.cgi?jobid=%s\n" % jobid)
    print("Content-type: text/html\n")
    print("<HTML>")
    print("<HEAD>")
    print("\t<TITLE>%s</TITLE>" % pagetitle)
    print("\t<link rel=\"stylesheet\" href=\"%s\" type=\"text/css\">\n" % STYLESHEET)
    print("</HEAD>")
    return


def mainCGI():
    """
        Opal driver for running PDB2PQR from a web page
    """
    global name, infile, ligandfilename, filename
    serviceURL = PDB2PQR_OPAL_URL

    cgitb.enable()
    form = cgi.FieldStorage()

    options = {}

    ff = form["FF"].value
    options["ff"] = ff
    fffile = None
    input = 0

    if "DEBUMP" in form:
        options["debump"] = 1
    else:
        options["debump"] = 0
    if "OPT" in form:
        options["opt"] = 1
    else:
        options["opt"] = 0
    if "PROPKA" in form:
        try:
            ph = float(form["PH"].value)
            if ph < 0.0 or ph > 14.0: raise ValueError
            options["ph"] = ph
        except ValueError:
            text = "The entered pH of %.2f is invalid!  " % form["PH"].value
            text += "Please choose a pH between 0.0 and 14.0."
            #             print "Content-type: text/html\n"
            print(text)
            sys.exit(2)
    if "PDBID" in form:
        filename = form["PDBID"].value
        infile = getPDBFile(form["PDBID"].value)
    elif "PDB" in form:
        filename = form["PDB"].filename
        filename = filename.split(r'[/\\]')[-1]
        infile = StringIO(form["PDB"].value)
    if "INPUT" in form:
        input = 1
        options["apbs"] = 1
    if "USERFF" in form:
        #        userff = StringIO(form["USERFF"].value)
        #        ff = "user-defined"
        #        options["userff"] = userff
        ffname = form["USERFF"].filename
        ffname = ffname.split(r'[/\\]')[-1]
        fffile = StringIO(form["USERFF"].value)
        options["ff"] = ffname
    if "FFOUT" in form:
        if form["FFOUT"].value != "internal":
            options["ffout"] = form["FFOUT"].value
    if "CHAIN" in form:
        options["chain"] = 1
    if "WHITESPACE" in form:
        options["whitespace"] = 1
    if "LIGAND" in form:
        ligandfilename = str(form["LIGAND"].filename)
        ligandfilename = ligandfilename.split(r'[/\\]')[-1]
        options["ligand"] = StringIO(form["LIGAND"].value)

    try:
        #        starttime = time.time()
        #        name = setID(starttime)
        name = filename
        ligandFile = None
        ffFile = None
        # begin SOAP changes
        # need to switch options from a dictionary to something resembling a command line query
        # such as --chain
        myopts = ""
        for key in options:
            if key == "opt":
                if options[key] == 0:
                    # user does not want optimization
                    key = "noopt"
                else:
                    # pdb2pqr optimizes by default, don't bother with flag
                    continue
            elif key == "debump":
                if options[key] == 0:
                    # user does not want debumping
                    key = "nodebump"
                else:
                    # pdb2pqr debumps by default, so change this flag to --nodebump
                    continue
            elif key == "ph":
                val = options[key]
                key = "with-ph=%s" % val
            elif key == "ffout":
                val = options[key]
                key = "ffout=%s" % val
            elif key == "ligand":
                val = ligandfilename
                key = "ligand=%s" % val
                ligandFile = ns0.InputFileType_Def('inputFile')
                ligandFile._name = val
                ligandFileTemp = open(options["ligand"], "r")
                ligandFileString = ligandFileTemp.read()
                ligandFileTemp.close()
                ligandFile._contents = ligandFileString
            elif key == "apbs":
                key = "apbs-input"
            elif key == "chain":
                key = "chain"
            elif key == "whitespace":
                key = "whitespace"
            elif key == "ff":
                val = options[key]
                key = "ff=%s" % val
                if fffile:
                    ffFile = ns0.InputFileType_Def('inputFile')
                    ffFile._name = val
                    ffFileTemp = open(fffile, "r")
                    ffFileString = ffFileTemp.read()
                    ffFileTemp.close()
                    ffFile._contents = ffFileString
            myopts += "--" + str(key) + " "
        myopts += str(filename) + " "
        myopts += "%s.pqr" % str(name)
        appLocator = AppServiceLocator()
        appServicePort = appLocator.getAppServicePort(serviceURL)
        # launch job
        req = launchJobRequest()
        req._argList = myopts
        inputFiles = []
        pdbFile = ns0.InputFileType_Def('inputFile')
        pdbFile._name = filename
        pdbFile._contents = infile.read()
        infile.close()
        inputFiles.append(pdbFile)
        if ligandFile:
            inputFiles.append(ligandFile)
        if ffFile:
            inputFiles.append(ffFile)
        req._inputFile = inputFiles
        try:
            resp = appServicePort.launchJob(req)
        except Exception as e:
            printheader("PDB2PQR Job Submission - Error")
            print("<BODY>\n<P>")
            print("There was an error with your job submission<br>")
            print("</P>\n</BODY>")
            print("</HTML>")
            sys.exit(2)
        printheader("PDB2PQR Job Submission", resp._jobID)

    except SystemError.StandardError as details:
        print(details)
        createError(name, details)


# File should only be called as CGI
mainCGI()
