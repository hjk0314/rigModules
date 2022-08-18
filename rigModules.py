from argparse import Namespace
from importlib.machinery import OPTIMIZED_BYTECODE_SUFFIXES
import maya.cmds as cmds
import maya.OpenMaya as om
import pymel.core as pm
import json
import os


# Creates a curve along the locator's trajectory.
# Place locators to create trajectories.
# If True is given to the closedCurve parameter, a circle is created.
def createCurveUsingLocator(closedCurve): # input : True or False
    sel = cmds.ls(sl=True) # select locators
    if not sel:
        om.MGlobal.displayWarning('Nothing selected.')
    else:
        chk = closedCurve
        locatorPosition = [cmds.xform(i, q=True, ws=True, rp=True) for i in sel] # every position of locators
        if not chk:
            cmds.curve(p=locatorPosition)
        else:
            # create circle first, and change their shape.
            circleName = cmds.circle(c=(0, 0, 0), nr=(0, 1, 0), sw=360, r=1, d=3, ch=False, s=len(sel))[0]
            for j, k in enumerate(locatorPosition):
                cmds.move(k[0], k[1], k[2], '%s.cv[%d]' % (circleName, j), ws=True)


# Returns the midpoint between two objects.
def getMiddlePoint(sel): # sel : tuple in list
    allPoints = [cmds.xform(i, q=True, t=True, ws=True) for i in sel]
    try:
        middlePoints = [(allPoints[0][i] + allPoints[1][i]) / 2 for i in range(3)] # ex) [1.0, -2.3, -0.4]
        return middlePoints
    except:
        return False


# Create a locator based on selection.
# This function uses the <getMiddlePoint> function.
# Create a locator at the origin if nothing is selected.
# Selecting one obj creates a locator in its place.
# When you select two obj, a locator is created at the midpoint.
def createLocatorMidpoint():
    sel = cmds.ls(sl=True, fl=True)
    selNumber = len(sel)
    if selNumber == 1: # Select One point.
        position = cmds.xform(sel[0], q=True, t=True, ws=True)
    elif selNumber == 2: # Select Two points.
        position = getMiddlePoint(sel)
    else:
        position = (0, 0, 0)
    locator = cmds.spaceLocator()
    cmds.xform(locator, t=position, ws=True)


# Add the name '_GRP' to the name and group it.
def grpOwnName(): # grouping itself and named own
    sel = cmds.ls(sl=True)
    if not sel:
        cmds.group(em=True) # em : empty
    else:
        for i in sel:
            cmds.group(i, n="%s_GRP" % i)


# Create channel attributes on a controller or group.
def createChannel(name, typ):
    sel = cmds.ls(sl=True)
    channelName = name
    channelType = typ # ex) "bool", "double"
    for ctrl in sel:
        channelChek = cmds.attributeQuery(channelName, node=ctrl, ex=True) # ex = exist
        if not channelChek:
            cmds.addAttr(ctrl, ln=channelName, at=channelType, dv=0)
            cmds.setAttr("%s.%s" % (ctrl, channelName), e=True, k=True)
        else:
            pass


 # input elements is fullPath or string.
 # ex1) "C:/Users/userName/Desktop/expressionSource.txt"
 # ex2) "tx = sin(time);"
def writeExpression(fullPath):
    ext = os.path.splitext(fullPath)[-1] # .txt
    chk = os.path.isfile(fullPath)
    if ext == ".txt" and chk: # ex1) fullPath
        with open(fullPath, 'r') as txt:
            srcList = txt.readlines()
        src = "".join(srcList)
    else: # ex2) string
        src = fullPath
    try:
        # s=string, o=object, ae=alwaysEvaluate, uc=unitConversion
        cmds.expression(s=src, o='', ae=1, uc='all')
    except:
        om.MGlobal.displayError('Fail to write expressions.')


# This function is Only works for strings sliced with underscores.
# When given a name like this : 'pCube1_22_obj_22_a2'
# Return index and its number.
# The number is last one in name.
def getNumberFromName(name): # input -> 'pCube1_22_obj_22_a2'
    nameSlice = name.split("_") # ['pCube1', '22', 'obj', '22', 'a2']
    digitList = [(j, k) for j, k in enumerate(nameSlice) if k.isdigit()] # [(1, '22'), (3, '22')]
    try:
        idx, num = digitList[-1]
        return idx, int(num)
    except:
        return False


# Attempt to delete unused plugins.
def deleteUnknownPlugins():
    cmds.delete(cmds.ls(type="unknown")) # Just delete Unknown type lists.
    pluginsList = cmds.unknownPlugin(q=True, l=True)
    if pluginsList:
        for j, k in enumerate(pluginsList):
            cmds.unknownPlugin(k, r=True)
            print("%d : %s" % (j, k)) # Print deleted plugin's names and number
        print('Delete completed.')
    else:
        om.MGlobal.displayWarning("There are no unknown plugins.")


# Create Curve on Path.
# This function works even if you select a point.
def createCurvePath(startFrame, endFrame):
    sel = cmds.ls(sl=True, fl=True)
    for j in sel:
        pointList = []
        for k in range(startFrame, endFrame + 1):
            cmds.currentTime(k)
            try:
                pointList.append(cmds.pointPosition(j)) # vtx position
            except:
                pointList.append(cmds.xform(j, q=True, ws=True, rp=True)) # obj position
        cmds.curve(p=pointList) # make Curves


# Offset the Keys
def keyOff(i=1): # i : interval
    sel = cmds.ls(sl=True, fl=True)
    for j, k in enumerate(sel):
        cmds.keyframe(k, e=True, r=True, tc = j * i)
    print("# ex : keyOff(5)")


# Move the key of the camera with the imagePlane, and adjust the frame offset to show the imagePlane accordingly.
def mapCameraKeyImage(destinationKey):
    sel = cmds.ls(sl=True, dag=True, type=['camera']) # ['cameraShape1']
    cam = cmds.listRelatives(sel, p=True) # ['camera1']
    try:
        currentKey = min(cmds.keyframe(cam, q=True)) # Smallest key value in camera.
        value = destinationKey - currentKey
    except:
        value = 0 # Nothing happens
        om.MGlobal.displayError("The camera has no keyframes.")
    img = cmds.listRelatives(sel, c=True) # ['imagePlane1']
    imgShape = cmds.listRelatives(img, c=True) # ['imagePlaneShape1']
    if img:
        cmds.keyframe(cam, e=True, r=True, tc=value)
        frameOffset = cmds.getAttr(imgShape[0] + ".frameOffset")
        cmds.setAttr(imgShape[0] + ".frameOffset", frameOffset - value)
    else:
        om.MGlobal.displayError("There is no imagePlane.")


# Create a curve controller.
# Create a shape with given arguments
def createCtrl(shape):
    ctrl = {
    "cub": [(-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5), (-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, -0.5, -0.5), (-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (0.5, -0.5, 0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5)], 
    "sph": [(0.0, 1.0, 0.0), (0.0, 0.707, 0.707), (0.0, 0.0, 1.0), (0.0, -0.707, 0.707), (0.0, -1.0, 0.0), (0.0, -0.707, -0.707), (0.0, 0.0, -1.0), (0.0, 0.707, -0.707), (0.0, 1.0, 0.0), (-0.707, 0.707, 0.0), (-1.0, 0.0, 0.0), (-0.707, 0.0, 0.707), (0.0, 0.0, 1.0), (0.707, 0.0, 0.707), (1.0, 0.0, 0.0), (0.707, 0.0, -0.707), (0.0, 0.0, -1.0), (-0.707, 0.0, -0.707), (-1.0, 0.0, 0.0), (-0.707, -0.707, 0.0), (0.0, -1.0, 0.0), (0.707, -0.707, 0.0), (1.0, 0.0, 0.0), (0.707, 0.707, 0.0), (0.0, 1.0, 0.0)], 
    "cyl": [(-1.0, 1.0, 0.0), (-0.707, 1.0, 0.707), (0.0, 1.0, 1.0), (0.707, 1.0, 0.707), (1.0, 1.0, 0.0), (0.707, 1.0, -0.707), (0.0, 1.0, -1.0), (0.0, 1.0, 1.0), (0.0, -1.0, 1.0), (-0.707, -1.0, 0.707), (-1.0, -1.0, 0.0), (-0.707, -1.0, -0.707), (0.0, -1.0, -1.0), (0.707, -1.0, -0.707), (1.0, -1.0, 0.0), (0.707, -1.0, 0.707), (0.0, -1.0, 1.0), (0.0, -1.0, -1.0), (0.0, 1.0, -1.0), (-0.7071, 1.0, -0.707), (-1.0, 1.0, 0.0), (1.0, 1.0, 0.0), (1.0, -1.0, 0.0), (-1.0, -1.0, 0.0), (-1.0, 1.0, 0.0)], 
    "pip": [(0.0, 1.0, 1), (0.0, -1.0, 1), (0.707, -1.0, 0.707), (1.0, -1.0, 0.0), (1.0, 1.0, 0.0), (0.707, 1.0, -0.707), (0.0, 1.0, -1), (0.0, -1.0, -1), (-0.707, -1.0, -0.707), (-1, -1.0, 0.0), (-1, 1.0, 0.0), (-0.707, 1.0, 0.707), (0.0, 1.0, 1), (0.707, 1.0, 0.707), (1.0, 1.0, 0.0), (1.0, -1.0, 0.0), (0.707, -1.0, -0.707), (0.0, -1.0, -1), (0.0, 1.0, -1), (-0.707, 1.0, -0.707), (-1, 1.0, 0.0), (-1, -1.0, 0.0), (-0.707, -1.0, 0.707), (0.0, -1.0, 1)], 
    "con": [(0.0, 2.0, 0.0), (-0.866, 0.0, -0.0), (0.866, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 1.0), (-0.866, 0.0, -0.0), (0.866, 0.0, 0.0), (0.0, 0.0, 1.0)], 
    "cir1": [(1.0, 1.0, 0.0), (0.924, 1.0, -0.383), (0.707, 1.0, -0.707), (0.383, 1.0, -0.924), (0, 1.0, -1.0), (0.226, 1.0, -1.075), (0.172, 1.0, -0.834), (0, 1.0, -1.0)], 
    "cir2": [(1.0, 1.0, 0.0), (0.866, 1.0, -0.5), (0.5, 1.0, -0.866), (0.0, 1.0, -1.0), (-0.5, 1.0, -0.866), (-0.866, 1.0, -0.5), (-1.0, 1.0, 0.0), (-1.087, 1.0, -0.299), (-0.772, 1.0, -0.204), (-1.0, 1.0, 0.0)], 
    "cir3": [(0.866, 1.0, -0.5), (0.5, 1.0, -0.866), (0.0, 1.0, -1.0), (-0.5, 1.0, -0.866), (-0.866, 1.0, -0.5), (-1.0, 1.0, 0.0), (-0.866, 1.0, 0.5), (-0.5, 1.0, 0.866), (0.0, 1.0, 1.0), (0.5, 1.0, 0.866), (0.866, 1.0, 0.5), (0.949, 1.0, 0.19), (0.949, 1.0, 0.19), (0.816, 1.0, 0.15), (1.0, 1.0, 0.0), (1.086, 1.0, 0.231), (0.949, 1.0, 0.19)], 
    "arr1": [(0.0, 0.0, 2.0), (2.0, 0.0, 1.0), (1.0, 0.0, 1.0), (1.0, 0.0, -2.0), (-1.0, 0.0, -2.0), (-1.0, 0.0, 1.0), (-2.0, 0.0, 1.0), (0.0, 0.0, 2.0)], 
    "arr2": [(0.0, 0.5, 2.0), (2.0, 0.5, 1.0), (1.0, 0.5, 1.0), (1.0, 0.5, -2.0), (-1.0, 0.5, -2.0), (-1.0, 0.5, 1.0), (-2.0, 0.5, 1.0), (0.0, 0.5, 2.0), (0.0, -0.5, 2.0), (2.0, -0.5, 1.0), (1.0, -0.5, 1.0), (1.0, -0.5, -2.0), (-1.0, -0.5, -2.0), (-1.0, -0.5, 1.0), (-2.0, -0.5, 1.0), (0.0, -0.5, 2.0), (2.0, -0.5, 1.0), (2.0, 0.5, 1.0), (1.0, 0.5, 1.0), (1.0, 0.5, -2.0), (1.0, -0.5, -2.0), (-1.0, -0.5, -2.0), (-1.0, 0.5, -2.0), (-1.0, 0.5, 1.0), (-2.0, 0.5, 1.0), (-2.0, -0.5, 1.0)]
    }
    try:
        cmds.curve(d=1, p=ctrl[shape])
    except:
        keyList = list(ctrl.keys())
        om.MGlobal.displayInfo(f"As input factors : {keyList}")


# Delete the node named 'vaccine_gene' and "breed_gene" in the <.ma> file.
# It is related to mayaScanner distributed by autodesk.
def deleteVaccineString(fullPath):
    vcc = "vaccine_gene"
    brd = "breed_gene"
    crt = "createNode"
    with open(fullPath, "r") as txt:
        lines = txt.readlines()
    vccList = [j for j, k in enumerate(lines) if vcc in k and crt in k] # List up the line numbers containing 'vaccine_gene'.
    brdList = [j for j, k in enumerate(lines) if brd in k and crt in k] # List up the line numbers containing 'breed_gene'.
    crtList = [j for j, k in enumerate(lines) if crt in k] # List up the line numbers containing 'createNode'.
    sum = vccList + brdList # ex) [16, 21, 84, 105]
    deleteList = []
    # List lines to delete consecutively
    for min in sum:
        max = crtList[crtList.index(min) + 1]
        deleteList += [i for i in range(min, max)]
    new, ext = os.path.splitext(fullPath)
    new += "_fixed" + ext
    # When creating a new file, delete the 'vaccine_gene' or 'breed_gene' paragraph.
    # Write '//Deleted here' instead of the deleted line.
    with open(new, "w") as txt:
        for j, k in enumerate(lines):
            if j in deleteList:
                txt.write("// Deleted here.\n")
            else:
                txt.write(k)


# Delete this file : "vaccine.py", "vaccine.pyc", "userSetup.py" in "C:/Users/user/Documents/maya/scripts/"
def deleteVaccineFiles():
    dir = cmds.internalVar(uad=True) + "scripts/"
    fileList = [dir + i for i in ["vaccine.py", "vaccine.pyc", "userSetup.py"]]
    for i in fileList:
        if os.path.isfile(i):
            os.remove(i)
        else:
            pass


# Checking First, if the file is infected or not.
def checkVaccineString(fullPath):        
    with open(fullPath, "r") as txt:
        lines = txt.readlines()
    result = ''
    for i in lines:
        if "vaccine_gene" in i or "breed_gene" in i:
            result = fullPath
            break
        else:
            pass
    return result


# using pymel.core
# Grabs only the given type from the selected group and returns the list.
def getTypeOnly(typ = "mesh"):
    if typ == "joint":
        shp = pm.ls(sl=True, dag=True, type=["joint"])
        obj = [i.name() for i in shp]
    else:
        shp = pm.ls(sl=True, dag=True, s=True)
        obj = [i.getParent().name() for i in shp if pm.nodeType(i) == "mesh"]
    pm.select(obj)
    lst = pm.ls(sl=True)
    return lst


# Delete Constraints and Break Connections scale and visibility.
def deleteConstraintAndConnection():
    sel = pm.ls(sl=True, type=["transform"])
    sel2 = [i for i in sel if not "Constraint" in pm.nodeType(i)]
    channelList = [".tx", ".ty", ".tz", ".rx", ".ry", ".rz", ".sx", ".sy", ".sz", ".v"]
    for i in sel2:
        for j in channelList:
            pm.setAttr(i + j, k=True, l=False)
            try:
                pm.disconnectAttr(i + j) # Break connections : scale, visibility
            except:
                pass
        pm.delete(i, cn=True)


# show drawStyle in joint attributes.
def setBoneDrawStyle(attr="drawStyle"):
    sel = pm.ls(sl=True)
    for i in sel:
        chkAttr = pm.attributeQuery(attr, node=i, ex=True)
        if chkAttr:
            pm.setAttr("%s.%s" % (i, attr), 0)
        else:
            pass


# Create a locator at the selected joint location.
# And return the locators list.
def createLocatorObjPosition():
    sel = pm.ls(sl=True)
    locatorList = []
    for i in sel:
        locator = pm.spaceLocator(n="%s_locator" % i, p=(0, 0, 0))
        pm.matchTransform(locator, i, pos=True)
        locatorList.append(locator)
    return locatorList


# Create an empty group and match the pivot with the selector.
def grpEmpty():
    sel = pm.ls(sl=True)
    for i in sel:
        grp = pm.group(em=True, n=i + "_offset")
        pm.matchTransform(grp, i, pos=True, rot=True)
        try:
            iParent = "".join(pm.listRelatives(i, p=True)) # Selector's mom group.
            pm.parent(grp, iParent)
        except:
            pass
        pm.parent(i, grp)


# return last number from name.
def getNumberFromName(name): # Input -> 'pCube1_22_obj_22_a2'
    nameList = name.split('_') # ['pCube1', '22', 'obj', '22', 'a2']
    digitLst = [(j, k) for j, k in enumerate(nameList) if k.isdigit()] # [(1, '22'), (3, '22')]
    try:
        index, number = digitLst[-1] # index = 3, number = '22'
        return int(number)
    except:
        return False


# Sets the color of the controller.
# idx : blue=6, red=13, yellow=17
def setColorRed(idx=13):
    sel = cmds.ls(sl=True, dag=True, s=True, type=["mesh"])
    for i in sel:
        cmds.setAttr(i + ".overrideEnabled", 1)
        cmds.setAttr(i + ".overrideColor", idx)


# keywords = ['json', 'os', 'getParent', 'shadingGroups', 'sets', 'fileDialog2', 'exportSelected', 'AbcExport', 'uery']
# author = "HONG JINKI"
# update = {'1st': '2022/05/10', '2nd': '2022/08/03'}
# Module name : hjkTool_ABC
# Description : Export to json file and shading networks. And assign to them.
class ABC():
    def __init__(self):
        min = pm.playbackOptions(q=True, min=True)
        max = pm.playbackOptions(q=True, max=True)
        self.setupUI(min, max)

    # UI.
    def setupUI(self, min, max):
        if pm.window('exportABC_withShader', exists=True):
            pm.deleteUI('exportABC_withShader')
        else:
            win = pm.window('exportABC_withShader', t='Export to Alembic with Shader', s=True, rtf=True)
            pm.columnLayout(cat=('both', 4), rowSpacing=2, columnWidth=380)
            pm.separator(h=10)
            pm.button(l='Create JSON and export shadingEngines', c=lambda x: self.jsonButton())
            self.frameRange = pm.intFieldGrp(l='Range : ', nf=2, v1=min, v2=max)
            self.oneFileCheck = pm.checkBoxGrp(l='One File : ', ncb=1, v1=True)
            pm.button(l='Export ABC', c=lambda x: self.exportButton())
            pm.button(l='Import ABC', c=lambda x: self.importButton())
            pm.button(l='Assign shaders to objects', c=lambda x: self.assignButton())
            pm.separator(h=10)
            pm.showWindow(win)

    # This function works when the json button is pressed.
    def jsonButton(self):
        sel = pm.ls(sl=True, dag=True, s=True)
        if not sel:
            om.MGlobal.displayError("Nothing Selected.")
        elif self.checkSameName(sel):
            om.MGlobal.displayError("Same name exists.")
        else:
            shdEngList = self.getShadingEngine(sel)
            jsonPath = pm.fileDialog2(fm=0, ff='json (*.json);; All Files (*.*)')
            if not jsonPath:
                om.MGlobal.displayInfo('Canceled.')
            else:
                jsonPath = ''.join(jsonPath)
                self.writeJson(shdEngList, jsonPath)
                self.exportShader(shdEngList, jsonPath)

    # If there is a "|" in the object name, it is considered a duplicate name.
    def checkSameName(self, nameList):
        sameName = [i for i in nameList if "|" in i]
        return sameName

    # If the object is connected to the shading engine, it is returned as a dictionary.
    def getShadingEngine(self, sel):
        dic = {}
        for i in sel:
            try:
                shadingEngine = i.shadingGroups()[0].name()
            except:
                continue
            objName = i.getParent().name()
            objName = objName.split(":")[-1] if ":" in objName else objName
            dic[objName] = shadingEngine
        return dic

    # Create a json file.
    def writeJson(self, dic, jsonPath):
        with open(jsonPath, 'w') as JSON:
            json.dump(dic, JSON, indent=4)

    # Export the shading network and save it as a .ma file.
    def exportShader(self, dic, fullPath):
        (dir, ext) = os.path.splitext(fullPath)
        exportPath = "%s_shader" % dir
        shdEngList = list(set(dic.values()))
        pm.select(cl=True)
        pm.select(shdEngList, ne=True)
        pm.exportSelected(exportPath, type="mayaAscii", f=True)

    # This function works when the Export button is pressed.
    def exportButton(self):
        sel = pm.ls(sl=True, long=True)
        # multiple abc files or one abc file. If True then one file.
        oneFileCheck = pm.checkBoxGrp(self.oneFileCheck, q=True, v1=True)
        fullPath = self.getExportPath(oneFileCheck)
        if not fullPath:
            om.MGlobal.displayInfo("Canceled.")
        else:
            if oneFileCheck:
                selection = ""
                for i in sel:
                    selection += " -root " + i
                exportOpt = self.createJstring(fullPath[0], selection)
                pm.AbcExport(j=exportOpt)
            else:
                for i in sel:
                    selection = " -root " + i
                    newPath = fullPath[0] + "/" + i + ".abc"
                    exportOpt = self.createJstring(newPath, selection)
                    pm.AbcExport(j=exportOpt)

    # Select a folder or specify a file name.
    def getExportPath(self, oneFileCheck):
        if oneFileCheck:
            abcPath = pm.fileDialog2(fm=0, ff='Alembic (*.abc);; All Files (*.*)')
        else:
            abcPath = pm.fileDialog2(fm=2, ds=1)
        return abcPath

    # Jstring is required to export.
    def createJstring(self, fullPath, selection):
        startFrame = pm.intFieldGrp(self.frameRange, q=True, v1=True)
        endFrame = pm.intFieldGrp(self.frameRange, q=True, v2=True)
        abc = " -file %s" % fullPath
        frameRange = "-frameRange %s %s" % (str(startFrame), str(endFrame))
        # ======= options start ==================================
        exportOpt = frameRange
        exportOpt += " -noNormals"
        exportOpt += " -ro"
        exportOpt += " -stripNamespaces"
        exportOpt += " -uvWrite"
        exportOpt += " -writeColorSets"
        exportOpt += " -writeFaceSets"
        exportOpt += " -wholeFrameGeo"
        exportOpt += " -worldSpace"
        exportOpt += " -writeVisibility"
        exportOpt += " -eulerFilter"
        exportOpt += " -autoSubd"
        exportOpt += " -writeUVSets"
        exportOpt += " -dataFormat ogawa"
        exportOpt += selection
        exportOpt += abc
        # ======= options end ====================================
        return exportOpt

    # This function works when the Import button is pressed. 
    def importButton(self):
        importDir = pm.fileDialog2(fm=1, ff='Alembic (*.abc);; All Files (*.*)')
        if importDir:
            pm.AbcImport(importDir, m='import')
        else:
            om.MGlobal.displayInfo("Canceled.")

    # This function works when the Assign button is pressed.
    # "_shader.ma" is loaded as a reference and associated with the selected object.
    def assignButton(self):
        sel = pm.ls(sl=True, dag=True, s=True)
        if not sel:
            om.MGlobal.displayError('Nothing selected.')
        else:
            jsonPath = pm.fileDialog2(fm=1, ff='json (*.json);; All Files (*.*)')
            shaderPath = self.getShaderPath(jsonPath)
            if not jsonPath:
                om.MGlobal.displayInfo("Canceled.")
            elif not shaderPath:
                om.MGlobal.displayError('There are no "_shader.ma" files.')
            else:
                self.makeReference(shaderPath)
                jsonDic = self.readJson(jsonPath)
                failLst = self.assignShd(sel, jsonDic)
                message = "Some objects failed to connect." if failLst else "Completed successfully."
                om.MGlobal.displayInfo(message)

    # Attempts to assign, and returns a list that fails.
    def assignShd(self, sel, jsonDic):
        assignFailed = []
        for i in sel:
            objName = i.getParent().name()
            sepName = objName.split(":")[-1] if ":" in objName else objName
            if sepName in jsonDic:
                try:
                    pm.sets(jsonDic[sepName], fe=objName)
                except:
                    assignFailed.append(objName)
            else:
                continue
        return assignFailed

    # Load Reference "_shader.ma" file.
    def makeReference(self, shaderPath):
        try:
            # If a reference aleady exists, get reference's node name.
            referenceName = pm.referenceQuery(shaderPath, referenceNode=True)
        except:
            referenceName = False
        if referenceName:
            # This is a replacement reference.
            # cmds.file(shaderPath, lr=referenceName, op='v=0')   # lr=loadReference
            pm.loadReference(shaderPath, op='v=0')
        else:
            # This is a new reference.
            # r=reference, iv=ignoreVersion, gl=groupLocator, mnc=mergeNamespacesOnClash, op=option, v=verbose, ns=nameSpace
            # cmds.file(shaderPath, r=True, typ='mayaAscii', iv=True, gl=True, mnc=True, op='v=0', ns=':')
            pm.createReference(shaderPath, r=True, typ='mayaAscii', iv=True, gl=True, mnc=True, op='v=0', ns=':')

    # Read shading information from Json file.
    def readJson(self, jsonPath):
        try:
            with open(jsonPath[0], 'r') as JSON:
                jsonDic = json.load(JSON)
            return jsonDic
        except:
            return False

    # There should be a "_shader.ma" file in the same folder as the json file.
    def getShaderPath(self, jsonPath):
        try:
            (dir, ext) = os.path.splitext(jsonPath[0])
            shaderPath = dir + "_shader.ma"
            checkFile = os.path.isfile(shaderPath)
            return shaderPath if checkFile else False
        except:
            return False


class bundangmain():
    def __init__(self):
        self.bundangmainA = {
            'init0': [0.0, 4.0], 'init1': [0.0, 7.0], 'init2': [0.0, 14.0], 'init3': [0.0, 16.0], 
            'inWall0': [0.0, 18.0], 'inWall1': [0.0, 22.0], 'inWall2': [0.0, 24.0], 'inWall3': [0.0, 26.0], 'inWall4': [0.0, 26.0], 'inWall5': [0.0, 43.0], 'inWall6': [0.0, 28.0], 'inWall7': [0.0, 34.0], 'inWall8': [0.0, 40.0], 'inWall9': [0.0, 43.0], 'inWall10': [0.0, 46.0], 'inWall11': [0.0, 52.0], 'inWall12': [0.0, 55.0], 'inWall13': [0.0, 61.0], 'inWall14': [0.0, 67.0], 'inWall15': [0.0, 73.0], 'inWall16': [0.0, 76.0], 'inWall17': [0.0, 79.0], 'inWall18': [0.0, 91.0], 'inWall19': [0.0, 95.0], 'inWall20': [0.0, 95.0], 'inWall21': [0.0, 97.0], 'inWall22': [0.0, 97.0], 'inWall23': [0.0, 101.0], 'inWall24': [0.0, 110.0], 'inWall25': [0.0, 112.0], 'inWall26': [0.0, 116.0], 
            'asibar0': [0.0, 26.0, 145.0], 'asibar1': [0.0, 26.0, 145.0], 'asibar2': [0.0, 18.0, 145.0], 'asibar3': [0.0, 26.0, 144.0], 'asibar4': [0.0, 26.0, 144.0], 'asibar5': [0.0, 37.0, 144.0], 'asibar6': [0.0, 26.0, 144.0], 'asibar7': [0.0, 18.0, 144.0], 'asibar8': [0.0, 26.0, 144.0], 'asibar9': [0.0, 16.0, 144.0], 'asibar10': [0.0, 18.0, 144.0], 'asibar11': [0.0, 20.0, 145.0], 'asibar12': [0.0, 37.0, 145.0], 'asibar13': [0.0, 37.0, 145.0], 'asibar14': [0.0, 18.0, 144.0], 'asibar15': [0.0, 16.0, 144.0], 'asibar16': [0.0, 18.0, 144.0], 'asibar17': [0.0, 18.0, 145.0], 'asibar18': [0.0, 16.0, 145.0], 'asibar19': [0.0, 10.0, 145.0], 'asibar20': [0.0, 18.0, 145.0], 'asibar21': [0.0, 12.0, 144.0], 'asibar22': [0.0, 46.0, 142.0], 'asibar23': [0.0, 46.0, 143.0], 'asibar24': [0.0, 40.0, 143.0], 'asibar25': [0.0, 40.0, 142.0], 'asibar26': [0.0, 46.0, 142.0], 'asibar27': [0.0, 40.0, 143.0], 'asibar28': [0.0, 40.0, 142.0], 'asibar29': [0.0, 34.0, 143.0], 'asibar30': [0.0, 52.0, 142.0], 'asibar31': [0.0, 34.0, 143.0], 'asibar32': [0.0, 28.0, 143.0], 'asibar33': [0.0, 52.0, 142.0], 'asibar34': [0.0, 34.0, 143.0], 'asibar35': [0.0, 46.0, 142.0], 'asibar36': [0.0, 28.0, 142.0], 'asibar37': [0.0, 40.0, 143.0], 'asibar38': [0.0, 46.0, 142.0], 'asibar39': [0.0, 28.0, 142.0], 'asibar40': [0.0, 46.0, 142.0], 'asibar41': [0.0, 40.0, 143.0], 'asibar42': [0.0, 52.0, 142.0], 'asibar43': [0.0, 34.0, 143.0], 'asibar44': [0.0, 64.0, 140.0], 'asibar45': [0.0, 55.0, 140.0], 'asibar46': [0.0, 61.0, 141.0], 'asibar47': [0.0, 58.0, 140.0], 'asibar48': [0.0, 61.0, 140.0], 'asibar49': [0.0, 64.0, 140.0], 'asibar50': [0.0, 61.0, 141.0], 'asibar51': [0.0, 55.0, 140.0], 'asibar52': [0.0, 64.0, 140.0], 'asibar53': [0.0, 55.0, 140.0], 'asibar54': [0.0, 55.0, 141.0], 'asibar55': [0.0, 64.0, 141.0], 'asibar56': [0.0, 55.0, 141.0], 'asibar57': [0.0, 64.0, 141.0], 'asibar58': [0.0, 61.0, 141.0], 'asibar59': [0.0, 64.0, 140.0], 'asibar60': [0.0, 67.0, 141.0], 'asibar61': [0.0, 61.0, 140.0], 'asibar62': [0.0, 64.0, 140.0], 'asibar63': [0.0, 61.0, 140.0], 'asibar64': [0.0, 61.0, 141.0], 'asibar65': [0.0, 55.0, 141.0], 'asibar66': [0.0, 95.0, 139.0], 'asibar67': [0.0, 95.0, 138.0], 'asibar68': [0.0, 89.0, 138.0], 'asibar69': [0.0, 84.0, 138.0], 'asibar70': [0.0, 89.0, 139.0], 'asibar71': [0.0, 89.0, 139.0], 'asibar72': [0.0, 89.0, 138.0], 'asibar73': [0.0, 89.0, 139.0], 'asibar74': [0.0, 89.0, 138.0], 'asibar75': [0.0, 95.0, 138.0], 'asibar76': [0.0, 89.0, 139.0], 'asibar77': [0.0, 89.0, 138.0], 'asibar78': [0.0, 101.0, 139.0], 'asibar79': [0.0, 95.0, 138.0], 'asibar80': [0.0, 101.0, 138.0], 'asibar81': [0.0, 95.0, 138.0], 'asibar82': [0.0, 95.0, 139.0], 'asibar83': [0.0, 95.0, 138.0], 'asibar84': [0.0, 89.0, 139.0], 'asibar85': [0.0, 84.0, 138.0], 'asibar86': [0.0, 89.0, 139.0], 'asibar87': [0.0, 89.0, 139.0], 'asibar88': [0.0, 105.0, 134.0], 'asibar89': [0.0, 105.0, 134.0], 'asibar90': [0.0, 112.0, 134.0], 'asibar91': [0.0, 107.0, 134.0], 'asibar92': [0.0, 112.0, 134.0], 'asibar93': [0.0, 107.0, 134.0], 'asibar94': [0.0, 112.0, 134.0], 'asibar95': [0.0, 107.0, 134.0], 'asibar96': [0.0, 105.0, 134.0], 'asibar97': [0.0, 110.0, 134.0], 'asibar98': [0.0, 105.0, 134.0], 'asibar99': [0.0, 110.0, 134.0], 'asibar100': [0.0, 107.0, 134.0], 'asibar101': [0.0, 112.0, 134.0], 
            'structure0': [0.0, 31.0], 'structure1': [0.0, 26.0], 'structure2': [0.0, 49.0], 'structure3': [0.0, 43.0], 'structure4': [0.0, 87.0], 'structure5': [0.0, 79.0], 'structure6': [0.0, 101.0], 'structure7': [0.0, 97.0], 'structure8': [0.0, 114.0], 
            'fence0': [0.0, 40.0, 143.0], 'fence1': [0.0, 45.0, 72.0], 'fence2': [0.0, 45.0, 72.0], 'fence3': [0.0, 45.0, 72.0], 'fence4': [0.0, 45.0, 72.0], 'fence5': [0.0, 45.0, 72.0], 'fence6': [0.0, 46.0, 72.0], 'fence7': [0.0, 46.0, 72.0], 'fence8': [0.0, 44.0, 72.0], 'fence9': [0.0, 47.0, 72.0], 'fence10': [0.0, 44.0, 72.0], 'fence11': [0.0, 46.0, 72.0], 'fence12': [0.0, 45.0, 72.0], 'fence13': [0.0, 42.0, 143.0], 'fence14': [0.0, 64.0, 141.0], 'fence15': [0.0, 63.0, 142.0], 'fence16': [0.0, 68.0, 103.0], 'fence17': [0.0, 67.0, 103.0], 'fence18': [0.0, 65.0, 103.0], 'fence19': [0.0, 66.0, 103.0], 'fence20': [0.0, 65.0, 103.0], 'fence21': [0.0, 66.0, 103.0], 'fence22': [0.0, 65.0, 103.0], 'fence23': [0.0, 66.0, 103.0], 'fence24': [0.0, 67.0, 103.0], 'fence25': [0.0, 66.0, 103.0], 'fence26': [0.0, 69.0, 103.0], 'fence27': [0.0, 66.0, 103.0], 'fence28': [0.0, 95.0, 139.0], 'fence29': [0.0, 98.0, 119.0], 'fence30': [0.0, 99.0, 119.0], 'fence31': [0.0, 98.0, 119.0], 'fence32': [0.0, 98.0, 119.0], 'fence33': [0.0, 98.0, 119.0], 'fence34': [0.0, 97.0, 119.0], 'fence35': [0.0, 98.0, 119.0], 'fence36': [0.0, 98.0, 119.0], 'fence37': [0.0, 99.0, 119.0], 'fence38': [0.0, 97.0, 119.0], 'fence39': [0.0, 99.0, 119.0], 'fence40': [0.0, 97.0, 119.0], 'fence41': [0.0, 97.0, 140.0], 'fence42': [0.0, 112.0, 134.0], 'fence43': [0.0, 114.0, 134.0], 'fence44': [0.0, 112.0, 134.0], 'fence45': [0.0, 112.0, 134.0], 'fence46': [0.0, 113.0, 134.0], 'fence47': [0.0, 115.0, 134.0], 'fence48': [0.0, 114.0, 137.0], 
            'wall0': [0.0, 37.0], 'wall1': [0.0, 37.0], 'wall2': [0.0, 70.0], 'wall3': [0.0, 70.0], 'wall4': [0.0, 93.0], 'wall5': [0.0, 93.0], 'wall6': [0.0, 113.0], 'wall7': [0.0, 113.0], 'wall8': [0.0, 124.0], 
            'roof0': [0.0, 126.0], 'roof1': [0.0, 126.0], 'roof2': [0.0, 117.0]
        }
        self.bundangmainB = {
            'init0': [0.0, 5.0], 'init1': [0.0, 9.0], 'inWall0': [0.0, 13.0], 
            'inWall1': [0.0, 20.0], 'inWall2': [0.0, 26.0], 'inWall3': [0.0, 32.0], 'inWall4': [0.0, 38.0], 'inWall5': [0.0, 47.0], 'inWall6': [0.0, 50.0], 'inWall7': [0.0, 53.0], 'inWall8': [0.0, 65.0], 'inWall9': [0.0, 59.0], 'inWall10': [0.0, 65.0], 'inWall11': [0.0, 70.0], 'inWall12': [0.0, 70.0], 'inWall13': [0.0, 74.0], 'inWall14': [0.0, 80.0], 'inWall15': [0.0, 87.0], 'inWall16': [0.0, 90.0], 'inWall17': [0.0, 95.0], 'inWall18': [0.0, 98.0], 'inWall19': [0.0, 101.0], 'inWall20': [0.0, 105.0], 'inWall21': [0.0, 108.0], 'inWall22': [0.0, 111.0], 'inWall23': [0.0, 117.0], 
            'asibar0': [0.0, 13.0, 146.0], 'asibar1': [0.0, 13.0, 146.0], 'asibar2': [0.0, 13.0, 146.0], 'asibar3': [0.0, 13.0, 146.0], 'asibar4': [0.0, 13.0, 146.0], 'asibar5': [0.0, 13.0, 146.0], 'asibar6': [0.0, 13.0, 146.0], 'asibar7': [0.0, 13.0, 146.0], 'asibar8': [0.0, 13.0, 146.0], 'asibar9': [0.0, 13.0, 146.0], 'asibar10': [0.0, 13.0, 146.0], 'asibar11': [0.0, 17.0, 146.0], 'asibar12': [0.0, 17.0, 146.0], 'asibar13': [0.0, 17.0, 146.0], 'asibar14': [0.0, 17.0, 146.0], 'asibar15': [0.0, 17.0, 146.0], 'asibar16': [0.0, 17.0, 146.0], 'asibar17': [0.0, 17.0, 146.0], 'asibar18': [0.0, 29.0, 144.0], 'asibar19': [0.0, 29.0, 144.0], 'asibar20': [0.0, 29.0, 144.0], 'asibar21': [0.0, 29.0, 144.0], 'asibar22': [0.0, 29.0, 144.0], 'asibar23': [0.0, 29.0, 144.0], 'asibar24': [0.0, 29.0, 144.0], 'asibar25': [0.0, 29.0, 144.0], 'asibar26': [0.0, 29.0, 144.0], 'asibar27': [0.0, 38.0, 144.0], 'asibar28': [0.0, 38.0, 144.0], 'asibar29': [0.0, 38.0, 144.0], 'asibar30': [0.0, 38.0, 144.0], 'asibar31': [0.0, 38.0, 144.0], 'asibar32': [0.0, 38.0, 144.0], 'asibar33': [0.0, 38.0, 144.0], 'asibar34': [0.0, 38.0, 144.0], 'asibar35': [0.0, 38.0, 144.0], 'asibar36': [0.0, 44.0, 142.0], 'asibar37': [0.0, 44.0, 142.0], 'asibar38': [0.0, 44.0, 142.0], 'asibar39': [0.0, 44.0, 142.0], 'asibar40': [0.0, 44.0, 142.0], 'asibar41': [0.0, 44.0, 142.0], 'asibar42': [0.0, 44.0, 142.0], 'asibar43': [0.0, 44.0, 142.0], 'asibar44': [0.0, 44.0, 142.0], 'asibar45': [0.0, 50.0, 142.0], 'asibar46': [0.0, 50.0, 142.0], 'asibar47': [0.0, 50.0, 142.0], 'asibar48': [0.0, 50.0, 142.0], 'asibar49': [0.0, 50.0, 142.0], 'asibar50': [0.0, 50.0, 142.0], 'asibar51': [0.0, 50.0, 142.0], 'asibar52': [0.0, 50.0, 142.0], 'asibar53': [0.0, 50.0, 142.0], 'asibar54': [0.0, 59.0, 140.0], 'asibar55': [0.0, 59.0, 140.0], 'asibar56': [0.0, 59.0, 140.0], 'asibar57': [0.0, 59.0, 140.0], 'asibar58': [0.0, 59.0, 140.0], 'asibar59': [0.0, 59.0, 140.0], 'asibar60': [0.0, 59.0, 140.0], 'asibar61': [0.0, 59.0, 140.0], 'asibar62': [0.0, 59.0, 140.0], 'asibar63': [0.0, 65.0, 140.0], 'asibar64': [0.0, 65.0, 140.0], 'asibar65': [0.0, 65.0, 140.0], 'asibar66': [0.0, 65.0, 140.0], 'asibar67': [0.0, 65.0, 140.0], 'asibar68': [0.0, 65.0, 140.0], 'asibar69': [0.0, 65.0, 140.0], 'asibar70': [0.0, 65.0, 140.0], 'asibar71': [0.0, 65.0, 140.0], 'asibar72': [0.0, 68.0, 138.0], 'asibar73': [0.0, 68.0, 138.0], 'asibar74': [0.0, 68.0, 138.0], 'asibar75': [0.0, 68.0, 138.0], 'asibar76': [0.0, 68.0, 138.0], 'asibar77': [0.0, 68.0, 138.0], 'asibar78': [0.0, 68.0, 138.0], 'asibar79': [0.0, 70.0, 138.0], 'asibar80': [0.0, 70.0, 138.0], 'asibar81': [0.0, 70.0, 138.0], 'asibar82': [0.0, 70.0, 138.0], 'asibar83': [0.0, 70.0, 138.0], 'asibar84': [0.0, 70.0, 138.0], 'asibar85': [0.0, 70.0, 138.0], 'asibar86': [0.0, 70.0, 138.0], 'asibar87': [0.0, 70.0, 138.0], 'asibar88': [0.0, 70.0, 138.0], 'asibar89': [0.0, 70.0, 138.0], 'asibar90': [0.0, 81.0, 136.0], 'asibar91': [0.0, 81.0, 136.0], 'asibar92': [0.0, 81.0, 136.0], 'asibar93': [0.0, 81.0, 136.0], 'asibar94': [0.0, 81.0, 136.0], 'asibar95': [0.0, 81.0, 136.0], 'asibar96': [0.0, 81.0, 136.0], 'asibar97': [0.0, 81.0, 136.0], 'asibar98': [0.0, 81.0, 136.0], 'asibar99': [0.0, 84.0, 136.0], 'asibar100': [0.0, 84.0, 136.0], 'asibar101': [0.0, 84.0, 136.0], 'asibar102': [0.0, 84.0, 136.0], 'asibar103': [0.0, 84.0, 136.0], 'asibar104': [0.0, 84.0, 136.0], 'asibar105': [0.0, 84.0, 136.0], 'asibar106': [0.0, 84.0, 136.0], 'asibar107': [0.0, 84.0, 136.0], 'asibar108': [0.0, 95.0, 134.0], 'asibar109': [0.0, 95.0, 134.0], 'asibar110': [0.0, 95.0, 134.0], 'asibar111': [0.0, 95.0, 134.0], 'asibar112': [0.0, 95.0, 134.0], 'asibar113': [0.0, 95.0, 134.0], 'asibar114': [0.0, 95.0, 134.0], 'asibar115': [0.0, 95.0, 134.0], 'asibar116': [0.0, 98.0, 134.0], 'asibar117': [0.0, 98.0, 134.0], 'asibar118': [0.0, 98.0, 134.0], 'asibar119': [0.0, 98.0, 134.0], 'asibar120': [0.0, 98.0, 134.0], 'asibar121': [0.0, 98.0, 134.0], 'asibar122': [0.0, 98.0, 134.0], 'asibar123': [0.0, 98.0, 134.0], 'asibar124': [0.0, 98.0, 134.0], 'asibar125': [0.0, 98.0, 134.0], 'asibar126': [0.0, 105.0, 132.0], 'asibar127': [0.0, 105.0, 132.0], 'asibar128': [0.0, 105.0, 132.0], 'asibar129': [0.0, 105.0, 132.0], 'asibar130': [0.0, 105.0, 132.0], 'asibar131': [0.0, 105.0, 132.0], 'asibar132': [0.0, 105.0, 132.0], 'asibar133': [0.0, 105.0, 132.0], 'asibar134': [0.0, 105.0, 132.0], 'asibar135': [0.0, 108.0, 132.0], 'asibar136': [0.0, 108.0, 132.0], 'asibar137': [0.0, 108.0, 132.0], 'asibar138': [0.0, 108.0, 132.0], 'asibar139': [0.0, 108.0, 132.0], 'asibar140': [0.0, 108.0, 132.0], 'asibar141': [0.0, 108.0, 132.0], 'asibar142': [0.0, 108.0, 132.0], 'asibar143': [0.0, 108.0, 132.0], 
            'structure0': [0.0, 23.0], 'structure1': [0.0, 41.0], 'structure2': [0.0, 59.0], 'structure3': [0.0, 68.0], 'structure4': [0.0, 77.0], 'structure5': [0.0, 93.0], 'structure6': [0.0, 104.0], 'structure7': [0.0, 114.0], 
            'fence0': [0.0, 35.0, 145.0], 'fence1': [0.0, 42.0, 59.0], 'fence2': [0.0, 42.0, 59.0], 'fence3': [0.0, 42.0, 59.0], 'fence4': [0.0, 42.0, 59.0], 'fence5': [0.0, 42.0, 59.0], 'fence6': [0.0, 42.0, 59.0], 'fence7': [0.0, 42.0, 59.0], 'fence8': [0.0, 42.0, 59.0], 'fence9': [0.0, 43.0, 59.0], 'fence10': [0.0, 43.0, 59.0], 'fence11': [0.0, 43.0, 59.0], 'fence12': [0.0, 43.0, 59.0], 'fence13': [0.0, 43.0, 59.0], 'fence14': [0.0, 43.0, 59.0], 'fence15': [0.0, 43.0, 59.0], 'fence16': [0.0, 43.0, 59.0], 'fence17': [0.0, 53.0, 143.0], 'fence18': [0.0, 58.0, 70.0], 'fence19': [0.0, 58.0, 70.0], 'fence20': [0.0, 58.0, 70.0], 'fence21': [0.0, 58.0, 70.0], 'fence22': [0.0, 58.0, 70.0], 'fence23': [0.0, 58.0, 70.0], 'fence24': [0.0, 58.0, 70.0], 'fence25': [0.0, 58.0, 70.0], 'fence26': [0.0, 59.0, 70.0], 'fence27': [0.0, 59.0, 70.0], 'fence28': [0.0, 59.0, 70.0], 'fence29': [0.0, 59.0, 70.0], 'fence30': [0.0, 59.0, 70.0], 'fence31': [0.0, 59.0, 70.0], 'fence32': [0.0, 59.0, 70.0], 'fence33': [0.0, 59.0, 70.0], 'fence34': [0.0, 65.0, 141.0], 'fence35': [0.0, 69.0, 78.0], 'fence36': [0.0, 69.0, 78.0], 'fence37': [0.0, 69.0, 78.0], 'fence38': [0.0, 69.0, 78.0], 'fence39': [0.0, 69.0, 78.0], 'fence40': [0.0, 69.0, 78.0], 'fence41': [0.0, 69.0, 78.0], 'fence42': [0.0, 69.0, 78.0], 'fence43': [0.0, 70.0, 78.0], 'fence44': [0.0, 70.0, 78.0], 'fence45': [0.0, 70.0, 78.0], 'fence46': [0.0, 70.0, 78.0], 'fence47': [0.0, 70.0, 78.0], 'fence48': [0.0, 70.0, 78.0], 'fence49': [0.0, 70.0, 78.0], 'fence50': [0.0, 70.0, 78.0], 'fence51': [0.0, 74.0, 139.0], 'fence52': [0.0, 77.0, 94.0], 'fence53': [0.0, 77.0, 94.0], 'fence54': [0.0, 77.0, 94.0], 'fence55': [0.0, 77.0, 94.0], 'fence56': [0.0, 77.0, 94.0], 'fence57': [0.0, 77.0, 94.0], 'fence58': [0.0, 77.0, 94.0], 'fence59': [0.0, 77.0, 94.0], 'fence60': [0.0, 78.0, 94.0], 'fence61': [0.0, 78.0, 94.0], 'fence62': [0.0, 78.0, 94.0], 'fence63': [0.0, 78.0, 94.0], 'fence64': [0.0, 78.0, 94.0], 'fence65': [0.0, 78.0, 94.0], 'fence66': [0.0, 78.0, 94.0], 'fence67': [0.0, 78.0, 94.0], 'fence68': [0.0, 84.0, 137.0], 'fence69': [0.0, 93.0, 104.0], 'fence70': [0.0, 93.0, 104.0], 'fence71': [0.0, 93.0, 104.0], 'fence72': [0.0, 93.0, 104.0], 'fence73': [0.0, 93.0, 104.0], 'fence74': [0.0, 93.0, 104.0], 'fence75': [0.0, 93.0, 104.0], 'fence76': [0.0, 94.0, 104.0], 'fence77': [0.0, 94.0, 104.0], 'fence78': [0.0, 94.0, 104.0], 'fence79': [0.0, 94.0, 104.0], 'fence80': [0.0, 94.0, 104.0], 'fence81': [0.0, 94.0, 104.0], 'fence82': [0.0, 94.0, 104.0], 'fence83': [0.0, 94.0, 104.0], 'fence84': [0.0, 94.0, 104.0], 'fence85': [0.0, 98.0, 135.0], 'fence86': [0.0, 103.0, 115.0], 'fence87': [0.0, 103.0, 115.0], 'fence88': [0.0, 103.0, 115.0], 'fence89': [0.0, 103.0, 115.0], 'fence90': [0.0, 103.0, 115.0], 'fence91': [0.0, 103.0, 115.0], 'fence92': [0.0, 103.0, 115.0], 'fence93': [0.0, 103.0, 115.0], 'fence94': [0.0, 104.0, 115.0], 'fence95': [0.0, 104.0, 115.0], 'fence96': [0.0, 104.0, 115.0], 'fence97': [0.0, 104.0, 115.0], 'fence98': [0.0, 104.0, 115.0], 'fence99': [0.0, 104.0, 115.0], 'fence100': [0.0, 104.0, 115.0], 'fence101': [0.0, 104.0, 115.0], 'fence102': [0.0, 108.0, 133.0], 'fence103': [0.0, 114.0, 130.0], 'fence104': [0.0, 114.0, 130.0], 'fence105': [0.0, 114.0, 130.0], 'fence106': [0.0, 114.0, 130.0], 'fence107': [0.0, 114.0, 130.0], 'fence108': [0.0, 114.0, 130.0], 'fence109': [0.0, 114.0, 130.0], 'fence110': [0.0, 114.0, 130.0], 'fence111': [0.0, 115.0, 130.0], 'fence112': [0.0, 115.0, 130.0], 'fence113': [0.0, 115.0, 130.0], 'fence114': [0.0, 115.0, 130.0], 'fence115': [0.0, 115.0, 130.0], 'fence116': [0.0, 115.0, 130.0], 'fence117': [0.0, 115.0, 130.0], 'fence118': [0.0, 115.0, 130.0], 
            'wall0': [0.0, 29.0], 'wall1': [0.0, 50.0], 'wall2': [0.0, 65.0], 'wall3': [0.0, 74.0], 'wall4': [0.0, 87.0], 'wall5': [0.0, 101.0], 'wall6': [0.0, 111.0], 'wall7': [0.0, 120.0], 
            'roof0': [0.0, 121.0]
        }
        self.bundangmainC = {
            'init0': [0.0, 4.0], 'init1': [0.0, 7.0], 
            'inWall0': [0.0, 10.0], 'inWall1': [0.0, 13.0], 'inWall2': [0.0, 19.0], 'inWall3': [0.0, 19.0], 'inWall4': [0.0, 22.0], 'inWall5': [0.0, 28.0], 'inWall6': [0.0, 28.0], 'inWall7': [0.0, 34.0], 'inWall8': [0.0, 40.0], 'inWall9': [0.0, 40.0], 'inWall10': [0.0, 43.0], 'inWall11': [0.0, 49.0], 'inWall12': [0.0, 49.0], 'inWall13': [0.0, 52.0], 'inWall14': [0.0, 58.0], 'inWall15': [0.0, 61.0], 'inWall16': [0.0, 64.0], 'inWall17': [0.0, 70.0], 'inWall18': [0.0, 70.0], 'inWall19': [0.0, 73.0], 
            'asibar0': [0.0, 10.0, 104.0], 'asibar1': [0.0, 10.0, 104.0], 'asibar2': [0.0, 10.0, 104.0], 'asibar3': [0.0, 10.0, 104.0], 'asibar4': [0.0, 10.0, 104.0], 'asibar5': [0.0, 10.0, 104.0], 'asibar6': [0.0, 10.0, 104.0], 'asibar7': [0.0, 10.0, 104.0], 'asibar8': [0.0, 10.0, 104.0], 'asibar9': [0.0, 10.0, 104.0], 'asibar10': [0.0, 10.0, 104.0], 'asibar11': [0.0, 10.0, 104.0], 'asibar12': [0.0, 10.0, 104.0], 'asibar13': [0.0, 13.0, 104.0], 'asibar14': [0.0, 13.0, 104.0], 'asibar15': [0.0, 13.0, 104.0], 'asibar16': [0.0, 13.0, 104.0], 'asibar17': [0.0, 13.0, 104.0], 'asibar18': [0.0, 13.0, 104.0], 'asibar19': [0.0, 13.0, 104.0], 'asibar20': [0.0, 13.0, 104.0], 'asibar21': [0.0, 13.0, 104.0], 'asibar22': [0.0, 13.0, 104.0], 'asibar23': [0.0, 13.0, 104.0], 'asibar24': [0.0, 13.0, 104.0], 'asibar25': [0.0, 13.0, 104.0], 'asibar26': [0.0, 19.0, 102.0], 'asibar27': [0.0, 19.0, 102.0], 'asibar28': [0.0, 19.0, 102.0], 'asibar29': [0.0, 19.0, 102.0], 'asibar30': [0.0, 19.0, 102.0], 'asibar31': [0.0, 19.0, 102.0], 'asibar32': [0.0, 19.0, 102.0], 'asibar33': [0.0, 19.0, 102.0], 'asibar34': [0.0, 19.0, 102.0], 'asibar35': [0.0, 19.0, 102.0], 'asibar36': [0.0, 19.0, 102.0], 'asibar37': [0.0, 19.0, 102.0], 'asibar38': [0.0, 19.0, 102.0], 'asibar39': [0.0, 22.0, 102.0], 'asibar40': [0.0, 22.0, 102.0], 'asibar41': [0.0, 22.0, 102.0], 'asibar42': [0.0, 22.0, 102.0], 'asibar43': [0.0, 22.0, 102.0], 'asibar44': [0.0, 22.0, 102.0], 'asibar45': [0.0, 22.0, 102.0], 'asibar46': [0.0, 22.0, 102.0], 'asibar47': [0.0, 22.0, 102.0], 'asibar48': [0.0, 22.0, 102.0], 'asibar49': [0.0, 22.0, 102.0], 'asibar50': [0.0, 22.0, 102.0], 'asibar51': [0.0, 22.0, 102.0], 'asibar52': [0.0, 25.0, 100.0], 'asibar53': [0.0, 25.0, 100.0], 'asibar54': [0.0, 28.0, 100.0], 'asibar55': [0.0, 28.0, 100.0], 'asibar56': [0.0, 28.0, 100.0], 'asibar57': [0.0, 28.0, 100.0], 'asibar58': [0.0, 28.0, 100.0], 'asibar59': [0.0, 28.0, 100.0], 'asibar60': [0.0, 28.0, 100.0], 'asibar61': [0.0, 28.0, 100.0], 'asibar62': [0.0, 28.0, 100.0], 'asibar63': [0.0, 28.0, 100.0], 'asibar64': [0.0, 28.0, 100.0], 'asibar65': [0.0, 28.0, 100.0], 'asibar66': [0.0, 28.0, 100.0], 'asibar67': [0.0, 28.0, 100.0], 'asibar68': [0.0, 34.0, 100.0], 'asibar69': [0.0, 34.0, 100.0], 'asibar70': [0.0, 34.0, 100.0], 'asibar71': [0.0, 34.0, 100.0], 'asibar72': [0.0, 34.0, 100.0], 'asibar73': [0.0, 34.0, 100.0], 'asibar74': [0.0, 34.0, 100.0], 'asibar75': [0.0, 34.0, 100.0], 'asibar76': [0.0, 34.0, 100.0], 'asibar77': [0.0, 34.0, 100.0], 'asibar78': [0.0, 40.0, 98.0], 'asibar79': [0.0, 40.0, 98.0], 'asibar80': [0.0, 40.0, 98.0], 'asibar81': [0.0, 40.0, 98.0], 'asibar82': [0.0, 43.0, 98.0], 'asibar83': [0.0, 43.0, 98.0], 'asibar84': [0.0, 43.0, 98.0], 'asibar85': [0.0, 43.0, 98.0], 'asibar86': [0.0, 43.0, 98.0], 'asibar87': [0.0, 43.0, 98.0], 'asibar88': [0.0, 43.0, 98.0], 'asibar89': [0.0, 43.0, 98.0], 'asibar90': [0.0, 43.0, 98.0], 'asibar91': [0.0, 43.0, 98.0], 'asibar92': [0.0, 43.0, 98.0], 'asibar93': [0.0, 43.0, 98.0], 'asibar94': [0.0, 43.0, 98.0], 'asibar95': [0.0, 43.0, 98.0], 'asibar96': [0.0, 46.0, 98.0], 'asibar97': [0.0, 46.0, 98.0], 'asibar98': [0.0, 46.0, 98.0], 'asibar99': [0.0, 46.0, 98.0], 'asibar100': [0.0, 46.0, 98.0], 'asibar101': [0.0, 46.0, 98.0], 'asibar102': [0.0, 46.0, 98.0], 'asibar103': [0.0, 46.0, 98.0], 'asibar104': [0.0, 49.0, 96.0], 'asibar105': [0.0, 49.0, 96.0], 'asibar106': [0.0, 52.0, 96.0], 'asibar107': [0.0, 52.0, 96.0], 'asibar108': [0.0, 52.0, 96.0], 'asibar109': [0.0, 52.0, 96.0], 'asibar110': [0.0, 52.0, 96.0], 'asibar111': [0.0, 52.0, 96.0], 'asibar112': [0.0, 52.0, 96.0], 'asibar113': [0.0, 52.0, 96.0], 'asibar114': [0.0, 52.0, 96.0], 'asibar115': [0.0, 52.0, 96.0], 'asibar116': [0.0, 52.0, 96.0], 'asibar117': [0.0, 52.0, 96.0], 'asibar118': [0.0, 52.0, 96.0], 'asibar119': [0.0, 52.0, 96.0], 'asibar120': [0.0, 52.0, 96.0], 'asibar121': [0.0, 55.0, 96.0], 'asibar122': [0.0, 55.0, 96.0], 'asibar123': [0.0, 55.0, 96.0], 'asibar124': [0.0, 55.0, 96.0], 'asibar125': [0.0, 55.0, 96.0], 'asibar126': [0.0, 55.0, 96.0], 'asibar127': [0.0, 55.0, 96.0], 'asibar128': [0.0, 55.0, 96.0], 'asibar129': [0.0, 55.0, 96.0], 'asibar130': [0.0, 58.0, 94.0], 'asibar131': [0.0, 58.0, 94.0], 'asibar132': [0.0, 58.0, 94.0], 'asibar133': [0.0, 61.0, 94.0], 'asibar134': [0.0, 61.0, 94.0], 'asibar135': [0.0, 61.0, 94.0], 'asibar136': [0.0, 61.0, 94.0], 'asibar137': [0.0, 61.0, 94.0], 'asibar138': [0.0, 61.0, 94.0], 'asibar139': [0.0, 61.0, 94.0], 'asibar140': [0.0, 61.0, 94.0], 'asibar141': [0.0, 61.0, 94.0], 'asibar142': [0.0, 61.0, 94.0], 'asibar143': [0.0, 61.0, 94.0], 'asibar144': [0.0, 61.0, 94.0], 'asibar145': [0.0, 61.0, 94.0], 'asibar146': [0.0, 61.0, 94.0], 'asibar147': [0.0, 64.0, 94.0], 'asibar148': [0.0, 64.0, 94.0], 'asibar149': [0.0, 64.0, 94.0], 'asibar150': [0.0, 64.0, 94.0], 'asibar151': [0.0, 64.0, 94.0], 'asibar152': [0.0, 64.0, 94.0], 'asibar153': [0.0, 64.0, 94.0], 'asibar154': [0.0, 64.0, 94.0], 'asibar155': [0.0, 64.0, 94.0], 'asibar156': [0.0, 70.0, 92.0], 'asibar157': [0.0, 70.0, 92.0], 'asibar158': [0.0, 70.0, 92.0], 'asibar159': [0.0, 73.0, 92.0], 'asibar160': [0.0, 73.0, 92.0], 'asibar161': [0.0, 73.0, 92.0], 'asibar162': [0.0, 73.0, 92.0], 'asibar163': [0.0, 73.0, 92.0], 'asibar164': [0.0, 73.0, 92.0], 'asibar165': [0.0, 73.0, 92.0], 'asibar166': [0.0, 73.0, 92.0], 'asibar167': [0.0, 73.0, 92.0], 'asibar168': [0.0, 73.0, 92.0], 'asibar169': [0.0, 73.0, 92.0], 'asibar170': [0.0, 76.0, 92.0], 'asibar171': [0.0, 76.0, 92.0], 'asibar172': [0.0, 76.0, 92.0], 'asibar173': [0.0, 76.0, 92.0], 'asibar174': [0.0, 76.0, 92.0], 'asibar175': [0.0, 76.0, 92.0], 'asibar176': [0.0, 76.0, 92.0], 'asibar177': [0.0, 76.0, 92.0], 'asibar178': [0.0, 76.0, 92.0], 'asibar179': [0.0, 76.0, 92.0], 'asibar180': [0.0, 76.0, 92.0], 'asibar181': [0.0, 76.0, 92.0], 
            'structure0': [0.0, 16.0], 'structure1': [0.0, 25.0], 'structure2': [0.0, 37.0], 'structure3': [0.0, 46.0], 'structure4': [0.0, 55.0], 'structure5': [0.0, 67.0], 'structure6': [0.0, 76.0], 
            'fence0': [0.0, 19.0, 103.0], 'fence1': [0.0, 22.0, 36.0], 'fence2': [0.0, 22.0, 36.0], 'fence3': [0.0, 22.0, 36.0], 'fence4': [0.0, 22.0, 36.0], 'fence5': [0.0, 22.0, 36.0], 'fence6': [0.0, 22.0, 36.0], 'fence7': [0.0, 22.0, 36.0], 'fence8': [0.0, 22.0, 36.0], 'fence9': [0.0, 25.0, 36.0], 'fence10': [0.0, 25.0, 36.0], 'fence11': [0.0, 25.0, 36.0], 'fence12': [0.0, 25.0, 36.0], 'fence13': [0.0, 25.0, 36.0], 'fence14': [0.0, 25.0, 36.0], 'fence15': [0.0, 25.0, 36.0], 'fence16': [0.0, 25.0, 36.0], 'fence17': [0.0, 25.0, 36.0], 'fence18': [0.0, 31.0, 101.0], 'fence19': [0.0, 35.0, 49.0], 'fence20': [0.0, 35.0, 49.0], 'fence21': [0.0, 35.0, 49.0], 'fence22': [0.0, 35.0, 49.0], 'fence23': [0.0, 35.0, 49.0], 'fence24': [0.0, 35.0, 49.0], 'fence25': [0.0, 35.0, 49.0], 'fence26': [0.0, 38.0, 49.0], 'fence27': [0.0, 38.0, 49.0], 'fence28': [0.0, 38.0, 49.0], 'fence29': [0.0, 38.0, 49.0], 'fence30': [0.0, 38.0, 49.0], 'fence31': [0.0, 38.0, 49.0], 'fence32': [0.0, 38.0, 49.0], 'fence33': [0.0, 38.0, 49.0], 'fence34': [0.0, 38.0, 49.0], 'fence35': [0.0, 38.0, 49.0], 'fence36': [0.0, 43.0, 99.0], 'fence37': [0.0, 46.0, 58.0], 'fence38': [0.0, 46.0, 58.0], 'fence39': [0.0, 46.0, 58.0], 'fence40': [0.0, 46.0, 58.0], 'fence41': [0.0, 46.0, 58.0], 'fence42': [0.0, 46.0, 58.0], 'fence43': [0.0, 46.0, 58.0], 'fence44': [0.0, 46.0, 58.0], 'fence45': [0.0, 49.0, 58.0], 'fence46': [0.0, 49.0, 58.0], 'fence47': [0.0, 49.0, 58.0], 'fence48': [0.0, 49.0, 58.0], 'fence49': [0.0, 49.0, 58.0], 'fence50': [0.0, 49.0, 58.0], 'fence51': [0.0, 49.0, 58.0], 'fence52': [0.0, 49.0, 58.0], 'fence53': [0.0, 49.0, 58.0], 'fence54': [0.0, 52.0, 97.0], 'fence55': [0.0, 55.0, 70.0], 'fence56': [0.0, 55.0, 70.0], 'fence57': [0.0, 55.0, 70.0], 'fence58': [0.0, 55.0, 70.0], 'fence59': [0.0, 55.0, 70.0], 'fence60': [0.0, 55.0, 70.0], 'fence61': [0.0, 55.0, 70.0], 'fence62': [0.0, 55.0, 70.0], 'fence63': [0.0, 55.0, 70.0], 'fence64': [0.0, 58.0, 70.0], 'fence65': [0.0, 58.0, 70.0], 'fence66': [0.0, 58.0, 70.0], 'fence67': [0.0, 58.0, 70.0], 'fence68': [0.0, 58.0, 70.0], 'fence69': [0.0, 58.0, 70.0], 'fence70': [0.0, 58.0, 70.0], 'fence71': [0.0, 58.0, 70.0], 'fence72': [0.0, 58.0, 95.0], 'fence73': [0.0, 67.0, 79.0], 'fence74': [0.0, 67.0, 79.0], 'fence75': [0.0, 67.0, 79.0], 'fence76': [0.0, 67.0, 79.0], 'fence77': [0.0, 67.0, 79.0], 'fence78': [0.0, 67.0, 79.0], 'fence79': [0.0, 67.0, 79.0], 'fence80': [0.0, 70.0, 79.0], 'fence81': [0.0, 70.0, 79.0], 'fence82': [0.0, 70.0, 79.0], 'fence83': [0.0, 70.0, 79.0], 'fence84': [0.0, 70.0, 79.0], 'fence85': [0.0, 70.0, 79.0], 'fence86': [0.0, 70.0, 79.0], 'fence87': [0.0, 70.0, 79.0], 'fence88': [0.0, 70.0, 79.0], 'fence89': [0.0, 70.0, 79.0], 'fence90': [0.0, 73.0, 93.0], 'fence91': [0.0, 76.0, 90.0], 'fence92': [0.0, 76.0, 90.0], 'fence93': [0.0, 76.0, 90.0], 'fence94': [0.0, 76.0, 90.0], 'fence95': [0.0, 76.0, 90.0], 'fence96': [0.0, 76.0, 90.0], 'fence97': [0.0, 79.0, 90.0], 'fence98': [0.0, 79.0, 90.0], 'fence99': [0.0, 79.0, 90.0], 'fence100': [0.0, 79.0, 90.0], 'fence101': [0.0, 79.0, 90.0], 'fence102': [0.0, 79.0, 90.0], 'fence103': [0.0, 79.0, 90.0], 'fence104': [0.0, 79.0, 90.0], 'fence105': [0.0, 79.0, 90.0], 'fence106': [0.0, 79.0, 90.0], 'fence107': [0.0, 79.0, 90.0], 
            'wall0': [0.0, 22.0], 'wall1': [0.0, 28.0], 'wall2': [0.0, 43.0], 'wall3': [0.0, 52.0], 'wall4': [0.0, 61.0], 'wall5': [0.0, 73.0], 'wall6': [0.0, 82.0], 
            'roof0': [0.0, 81.0]
        }
        self.bundangmainD = {
            'init0': [0.0, 3.0], 'init1': [0.0, 6.0], 
            'inWall0': [0.0, 10.0], 'inWall1': [0.0, 13.0], 'inWall2': [0.0, 19.0], 'inWall3': [0.0, 22.0], 'inWall4': [0.0, 25.0], 'inWall5': [0.0, 31.0], 'inWall6': [0.0, 34.0], 'inWall7': [0.0, 37.0], 'inWall8': [0.0, 43.0], 'inWall9': [0.0, 46.0], 'inWall10': [0.0, 49.0], 'inWall11': [0.0, 55.0], 'inWall12': [0.0, 58.0], 'inWall13': [0.0, 61.0], 'inWall14': [0.0, 67.0], 'inWall15': [0.0, 70.0], 
            'asibar0': [0.0, 7.0, 102.0], 'asibar1': [0.0, 7.0, 102.0], 'asibar2': [0.0, 10.0, 102.0], 'asibar3': [0.0, 10.0, 102.0], 'asibar4': [0.0, 10.0, 102.0], 'asibar5': [0.0, 10.0, 102.0], 'asibar6': [0.0, 10.0, 102.0], 'asibar7': [0.0, 13.0, 102.0], 'asibar8': [0.0, 13.0, 102.0], 'asibar9': [0.0, 13.0, 102.0], 'asibar10': [0.0, 13.0, 102.0], 'asibar11': [0.0, 13.0, 102.0], 'asibar12': [0.0, 13.0, 102.0], 'asibar13': [0.0, 13.0, 102.0], 'asibar14': [0.0, 19.0, 98.0], 'asibar15': [0.0, 19.0, 98.0], 'asibar16': [0.0, 19.0, 98.0], 'asibar17': [0.0, 22.0, 98.0], 'asibar18': [0.0, 22.0, 98.0], 'asibar19': [0.0, 22.0, 98.0], 'asibar20': [0.0, 22.0, 98.0], 'asibar21': [0.0, 22.0, 98.0], 'asibar22': [0.0, 25.0, 98.0], 'asibar23': [0.0, 25.0, 98.0], 'asibar24': [0.0, 25.0, 98.0], 'asibar25': [0.0, 25.0, 98.0], 'asibar26': [0.0, 25.0, 98.0], 'asibar27': [0.0, 25.0, 98.0], 'asibar28': [0.0, 31.0, 94.0], 'asibar29': [0.0, 34.0, 94.0], 'asibar30': [0.0, 34.0, 94.0], 'asibar31': [0.0, 34.0, 94.0], 'asibar32': [0.0, 34.0, 94.0], 'asibar33': [0.0, 34.0, 94.0], 'asibar34': [0.0, 34.0, 94.0], 'asibar35': [0.0, 37.0, 94.0], 'asibar36': [0.0, 37.0, 94.0], 'asibar37': [0.0, 37.0, 94.0], 'asibar38': [0.0, 37.0, 94.0], 'asibar39': [0.0, 37.0, 94.0], 'asibar40': [0.0, 37.0, 94.0], 'asibar41': [0.0, 37.0, 94.0], 'asibar42': [0.0, 43.0, 90.0], 'asibar43': [0.0, 46.0, 90.0], 'asibar44': [0.0, 46.0, 90.0], 'asibar45': [0.0, 46.0, 90.0], 'asibar46': [0.0, 46.0, 90.0], 'asibar47': [0.0, 46.0, 90.0], 'asibar48': [0.0, 46.0, 90.0], 'asibar49': [0.0, 49.0, 90.0], 'asibar50': [0.0, 49.0, 90.0], 'asibar51': [0.0, 49.0, 90.0], 'asibar52': [0.0, 49.0, 90.0], 'asibar53': [0.0, 49.0, 90.0], 'asibar54': [0.0, 49.0, 90.0], 'asibar55': [0.0, 49.0, 90.0], 'asibar56': [0.0, 55.0, 86.0], 'asibar57': [0.0, 58.0, 86.0], 'asibar58': [0.0, 58.0, 86.0], 'asibar59': [0.0, 58.0, 86.0], 'asibar60': [0.0, 58.0, 86.0], 'asibar61': [0.0, 58.0, 86.0], 'asibar62': [0.0, 58.0, 86.0], 'asibar63': [0.0, 61.0, 86.0], 'asibar64': [0.0, 61.0, 86.0], 'asibar65': [0.0, 61.0, 86.0], 'asibar66': [0.0, 61.0, 86.0], 'asibar67': [0.0, 61.0, 86.0], 'asibar68': [0.0, 61.0, 86.0], 'asibar69': [0.0, 61.0, 86.0], 'asibar70': [0.0, 67.0, 82.0], 'asibar71': [0.0, 67.0, 82.0], 'asibar72': [0.0, 67.0, 82.0], 'asibar73': [0.0, 67.0, 82.0], 'asibar74': [0.0, 67.0, 82.0], 'asibar75': [0.0, 67.0, 82.0], 'asibar76': [0.0, 67.0, 82.0], 'asibar77': [0.0, 70.0, 82.0], 'asibar78': [0.0, 70.0, 82.0], 'asibar79': [0.0, 70.0, 82.0], 'asibar80': [0.0, 70.0, 82.0], 'asibar81': [0.0, 70.0, 82.0], 'asibar82': [0.0, 73.0, 82.0], 'asibar83': [0.0, 73.0, 82.0], 
            'structure0': [0.0, 16.0], 'structure1': [0.0, 28.0], 'structure2': [0.0, 40.0], 'structure3': [0.0, 52.0], 'structure4': [0.0, 64.0], 'structure5': [0.0, 73.0], 
            'fence0': [0.0, 16.0, 100.0], 'fence1': [0.0, 25.0, 40.0], 'fence2': [0.0, 25.0, 40.0], 'fence3': [0.0, 25.0, 40.0], 'fence4': [0.0, 25.0, 40.0], 'fence5': [0.0, 25.0, 40.0], 'fence6': [0.0, 25.0, 40.0], 'fence7': [0.0, 25.0, 40.0], 'fence8': [0.0, 28.0, 40.0], 'fence9': [0.0, 28.0, 40.0], 'fence10': [0.0, 28.0, 40.0], 'fence11': [0.0, 28.0, 40.0], 'fence12': [0.0, 28.0, 40.0], 'fence13': [0.0, 28.0, 40.0], 'fence14': [0.0, 28.0, 40.0], 'fence15': [0.0, 31.0, 96.0], 'fence16': [0.0, 37.0, 52.0], 'fence17': [0.0, 37.0, 52.0], 'fence18': [0.0, 37.0, 52.0], 'fence19': [0.0, 37.0, 52.0], 'fence20': [0.0, 37.0, 52.0], 'fence21': [0.0, 37.0, 52.0], 'fence22': [0.0, 40.0, 52.0], 'fence23': [0.0, 40.0, 52.0], 'fence24': [0.0, 40.0, 52.0], 'fence25': [0.0, 40.0, 52.0], 'fence26': [0.0, 40.0, 52.0], 'fence27': [0.0, 40.0, 52.0], 'fence28': [0.0, 40.0, 52.0], 'fence29': [0.0, 40.0, 52.0], 'fence30': [0.0, 43.0, 92.0], 'fence31': [0.0, 49.0, 64.0], 'fence32': [0.0, 49.0, 64.0], 'fence33': [0.0, 49.0, 64.0], 'fence34': [0.0, 49.0, 64.0], 'fence35': [0.0, 49.0, 64.0], 'fence36': [0.0, 49.0, 64.0], 'fence37': [0.0, 49.0, 64.0], 'fence38': [0.0, 52.0, 64.0], 'fence39': [0.0, 52.0, 64.0], 'fence40': [0.0, 52.0, 64.0], 'fence41': [0.0, 52.0, 64.0], 'fence42': [0.0, 52.0, 64.0], 'fence43': [0.0, 52.0, 64.0], 'fence44': [0.0, 52.0, 64.0], 'fence45': [0.0, 55.0, 88.0], 'fence46': [0.0, 61.0, 73.0], 'fence47': [0.0, 61.0, 73.0], 'fence48': [0.0, 61.0, 73.0], 'fence49': [0.0, 61.0, 73.0], 'fence50': [0.0, 61.0, 73.0], 'fence51': [0.0, 61.0, 73.0], 'fence52': [0.0, 61.0, 73.0], 'fence53': [0.0, 64.0, 73.0], 'fence54': [0.0, 64.0, 73.0], 'fence55': [0.0, 64.0, 73.0], 'fence56': [0.0, 64.0, 73.0], 'fence57': [0.0, 64.0, 73.0], 'fence58': [0.0, 64.0, 73.0], 'fence59': [0.0, 64.0, 73.0], 'fence60': [0.0, 67.0, 84.0], 'fence61': [0.0, 70.0, 80.0], 'fence62': [0.0, 70.0, 80.0], 'fence63': [0.0, 70.0, 80.0], 'fence64': [0.0, 70.0, 80.0], 'fence65': [0.0, 70.0, 80.0], 'fence66': [0.0, 70.0, 80.0], 'fence67': [0.0, 70.0, 80.0], 'fence68': [0.0, 73.0, 80.0], 'fence69': [0.0, 73.0, 80.0], 'fence70': [0.0, 73.0, 80.0], 'fence71': [0.0, 73.0, 80.0], 'fence72': [0.0, 73.0, 80.0], 'fence73': [0.0, 73.0, 80.0], 'fence74': [0.0, 73.0, 80.0], 
            'wall0': [0.0, 26.0], 'wall1': [0.0, 37.0], 'wall2': [0.0, 49.0], 'wall3': [0.0, 61.0], 'wall4': [0.0, 68.0], 'wall5': [0.0, 73.0], 
            'roof0': [0.0, 76.0]
        }
        self.bundangmainE = {
            'init0': [0.0, 3.0], 'init1': [0.0, 6.0], 
            'inWall0': [0.0, 9.0], 'inWall1': [0.0, 12.0], 'inWall2': [0.0, 18.0], 'inWall3': [0.0, 24.0], 'inWall4': [0.0, 27.0], 'inWall5': [0.0, 33.0], 'inWall6': [0.0, 39.0], 'inWall7': [0.0, 42.0], 'inWall8': [0.0, 48.0], 'inWall9': [0.0, 51.0], 
            'asibar0': [0.0, 6.0, 80.0], 'asibar1': [0.0, 6.0, 80.0], 'asibar2': [0.0, 9.0, 80.0], 'asibar3': [0.0, 9.0, 80.0], 'asibar4': [0.0, 9.0, 80.0], 'asibar5': [0.0, 9.0, 80.0], 'asibar6': [0.0, 12.0, 80.0], 'asibar7': [0.0, 12.0, 80.0], 'asibar8': [0.0, 12.0, 80.0], 'asibar9': [0.0, 12.0, 80.0], 'asibar10': [0.0, 12.0, 80.0], 'asibar11': [0.0, 12.0, 80.0], 'asibar12': [0.0, 12.0, 80.0], 'asibar13': [0.0, 12.0, 80.0], 'asibar14': [0.0, 21.0, 76.0], 'asibar15': [0.0, 21.0, 76.0], 'asibar16': [0.0, 24.0, 76.0], 'asibar17': [0.0, 24.0, 76.0], 'asibar18': [0.0, 24.0, 76.0], 'asibar19': [0.0, 24.0, 76.0], 'asibar20': [0.0, 24.0, 76.0], 'asibar21': [0.0, 24.0, 76.0], 'asibar22': [0.0, 24.0, 76.0], 'asibar23': [0.0, 24.0, 76.0], 'asibar24': [0.0, 27.0, 76.0], 'asibar25': [0.0, 27.0, 76.0], 'asibar26': [0.0, 27.0, 76.0], 'asibar27': [0.0, 27.0, 76.0], 'asibar28': [0.0, 36.0, 72.0], 'asibar29': [0.0, 39.0, 72.0], 'asibar30': [0.0, 39.0, 72.0], 'asibar31': [0.0, 39.0, 72.0], 'asibar32': [0.0, 39.0, 72.0], 'asibar33': [0.0, 39.0, 72.0], 'asibar34': [0.0, 42.0, 72.0], 'asibar35': [0.0, 42.0, 72.0], 'asibar36': [0.0, 42.0, 72.0], 'asibar37': [0.0, 42.0, 72.0], 'asibar38': [0.0, 42.0, 72.0], 'asibar39': [0.0, 42.0, 72.0], 'asibar40': [0.0, 42.0, 72.0], 'asibar41': [0.0, 42.0, 72.0], 'asibar42': [0.0, 51.0, 68.0], 'asibar43': [0.0, 51.0, 68.0], 'asibar44': [0.0, 51.0, 68.0], 'asibar45': [0.0, 54.0, 68.0], 'asibar46': [0.0, 54.0, 68.0], 'asibar47': [0.0, 54.0, 68.0], 'asibar48': [0.0, 54.0, 68.0], 'asibar49': [0.0, 54.0, 68.0], 'asibar50': [0.0, 57.0, 68.0], 'asibar51': [0.0, 57.0, 68.0], 'asibar52': [0.0, 57.0, 68.0], 'asibar53': [0.0, 57.0, 68.0], 'asibar54': [0.0, 57.0, 68.0], 'asibar55': [0.0, 57.0, 68.0], 
            'structure0': [0.0, 15.0], 'structure1': [0.0, 30.0], 'structure2': [0.0, 45.0], 'structure3': [0.0, 54.0], 
            'fence0': [0.0, 18.0, 78.0], 'fence1': [0.0, 30.0, 45.0], 'fence2': [0.0, 30.0, 45.0], 'fence3': [0.0, 30.0, 45.0], 'fence4': [0.0, 30.0, 45.0], 'fence5': [0.0, 30.0, 45.0], 'fence6': [0.0, 33.0, 45.0], 'fence7': [0.0, 33.0, 45.0], 'fence8': [0.0, 33.0, 45.0], 'fence9': [0.0, 33.0, 45.0], 'fence10': [0.0, 33.0, 45.0], 'fence11': [0.0, 33.0, 45.0], 'fence12': [0.0, 33.0, 45.0], 'fence13': [0.0, 36.0, 74.0], 'fence14': [0.0, 42.0, 57.0], 'fence15': [0.0, 42.0, 57.0], 'fence16': [0.0, 42.0, 57.0], 'fence17': [0.0, 42.0, 57.0], 'fence18': [0.0, 42.0, 57.0], 'fence19': [0.0, 45.0, 57.0], 'fence20': [0.0, 45.0, 57.0], 'fence21': [0.0, 45.0, 57.0], 'fence22': [0.0, 45.0, 57.0], 'fence23': [0.0, 45.0, 57.0], 'fence24': [0.0, 45.0, 57.0], 'fence25': [0.0, 45.0, 57.0], 'fence26': [0.0, 54.0, 66.0], 'fence27': [0.0, 54.0, 66.0], 'fence28': [0.0, 54.0, 66.0], 'fence29': [0.0, 54.0, 66.0], 'fence30': [0.0, 54.0, 66.0], 'fence31': [0.0, 48.0, 70.0], 'fence32': [0.0, 57.0, 66.0], 'fence33': [0.0, 57.0, 66.0], 'fence34': [0.0, 57.0, 66.0], 'fence35': [0.0, 57.0, 66.0], 'fence36': [0.0, 57.0, 66.0], 'fence37': [0.0, 57.0, 66.0], 'fence38': [0.0, 57.0, 66.0], 
            'wall0': [0.0, 24.0], 'wall1': [0.0, 36.0], 'wall2': [0.0, 48.0], 'wall3': [0.0, 57.0], 
            'roof0': [0.0, 60.0]
            }
        self.bundangmainF = {
            'init0': [0.0, 3.0], 'init1': [0.0, 6.0], 
            'inWall0': [0.0, 9.0], 'inWall1': [0.0, 12.0], 'inWall2': [0.0, 18.0], 'inWall3': [0.0, 24.0], 'inWall4': [0.0, 27.0], 'inWall5': [0.0, 33.0], 'inWall6': [0.0, 36.0], 'inWall7': [0.0, 39.0], 'inWall8': [0.0, 45.0], 'inWall9': [0.0, 48.0], 'inWall10': [0.0, 51.0], 'inWall11': [0.0, 57.0], 
            'asibar0': [0.0, 6.0, 84.0], 'asibar1': [0.0, 9.0, 84.0], 'asibar2': [0.0, 9.0, 84.0], 'asibar3': [0.0, 9.0, 84.0], 'asibar4': [0.0, 9.0, 84.0], 'asibar5': [0.0, 9.0, 84.0], 'asibar6': [0.0, 9.0, 84.0], 'asibar7': [0.0, 12.0, 84.0], 'asibar8': [0.0, 12.0, 84.0], 'asibar9': [0.0, 12.0, 84.0], 'asibar10': [0.0, 12.0, 84.0], 'asibar11': [0.0, 12.0, 84.0], 'asibar12': [0.0, 21.0, 80.0], 'asibar13': [0.0, 24.0, 80.0], 'asibar14': [0.0, 24.0, 80.0], 'asibar15': [0.0, 24.0, 80.0], 'asibar16': [0.0, 24.0, 80.0], 'asibar17': [0.0, 27.0, 80.0], 'asibar18': [0.0, 27.0, 80.0], 'asibar19': [0.0, 27.0, 80.0], 'asibar20': [0.0, 27.0, 80.0], 'asibar21': [0.0, 27.0, 80.0], 'asibar22': [0.0, 27.0, 80.0], 'asibar23': [0.0, 27.0, 80.0], 'asibar24': [0.0, 33.0, 76.0], 'asibar25': [0.0, 36.0, 76.0], 'asibar26': [0.0, 36.0, 76.0], 'asibar27': [0.0, 36.0, 76.0], 'asibar28': [0.0, 36.0, 76.0], 'asibar29': [0.0, 36.0, 76.0], 'asibar30': [0.0, 39.0, 76.0], 'asibar31': [0.0, 39.0, 76.0], 'asibar32': [0.0, 39.0, 76.0], 'asibar33': [0.0, 39.0, 76.0], 'asibar34': [0.0, 39.0, 76.0], 'asibar35': [0.0, 39.0, 76.0], 'asibar36': [0.0, 48.0, 72.0], 'asibar37': [0.0, 51.0, 72.0], 'asibar38': [0.0, 51.0, 72.0], 'asibar39': [0.0, 51.0, 72.0], 'asibar40': [0.0, 51.0, 72.0], 'asibar41': [0.0, 51.0, 72.0], 'asibar42': [0.0, 54.0, 72.0], 'asibar43': [0.0, 54.0, 72.0], 'asibar44': [0.0, 54.0, 72.0], 'asibar45': [0.0, 54.0, 72.0], 'asibar46': [0.0, 54.0, 72.0], 'asibar47': [0.0, 54.0, 72.0], 
            'structure0': [0.0, 15.0], 'structure1': [0.0, 30.0], 'structure2': [0.0, 42.0], 'structure3': [0.0, 54.0], 
            'fence0': [0.0, 18.0, 82.0], 'fence1': [0.0, 27.0, 42.0], 'fence2': [0.0, 27.0, 42.0], 'fence3': [0.0, 27.0, 42.0], 'fence4': [0.0, 27.0, 42.0], 'fence5': [0.0, 27.0, 42.0], 'fence6': [0.0, 27.0, 42.0], 'fence7': [0.0, 30.0, 42.0], 'fence8': [0.0, 30.0, 42.0], 'fence9': [0.0, 30.0, 42.0], 'fence10': [0.0, 30.0, 42.0], 'fence11': [0.0, 30.0, 42.0], 'fence12': [0.0, 30.0, 42.0], 'fence13': [0.0, 33.0, 78.0], 'fence14': [0.0, 39.0, 54.0], 'fence15': [0.0, 39.0, 54.0], 'fence16': [0.0, 39.0, 54.0], 'fence17': [0.0, 39.0, 54.0], 'fence18': [0.0, 39.0, 54.0], 'fence19': [0.0, 39.0, 54.0], 'fence20': [0.0, 42.0, 54.0], 'fence21': [0.0, 42.0, 54.0], 'fence22': [0.0, 42.0, 54.0], 'fence23': [0.0, 42.0, 54.0], 'fence24': [0.0, 42.0, 54.0], 'fence25': [0.0, 42.0, 54.0], 'fence26': [0.0, 45.0, 74.0], 'fence27': [0.0, 51.0, 70.0], 'fence28': [0.0, 51.0, 70.0], 'fence29': [0.0, 51.0, 70.0], 'fence30': [0.0, 51.0, 70.0], 'fence31': [0.0, 51.0, 70.0], 'fence32': [0.0, 54.0, 70.0], 'fence33': [0.0, 54.0, 70.0], 'fence34': [0.0, 54.0, 70.0], 'fence35': [0.0, 54.0, 70.0], 'fence36': [0.0, 54.0, 70.0], 'fence37': [0.0, 54.0, 70.0], 'fence38': [0.0, 54.0, 70.0], 
            'wall0': [0.0, 24.0], 'wall1': [0.0, 33.0], 'wall2': [0.0, 45.0], 'wall3': [0.0, 57.0], 
            'roof0': [0.0, 60.0]
            }
        self.setupUI()

    # UI.
    def setupUI(self):
        if pm.window('Bundang_Structure', exists=True):
            pm.deleteUI('Bundang_Structure')
        else:
            win = pm.window('Bundang_Structure', t='Auto Build Up', s=True, rtf=True)
            pm.columnLayout(cat=('both', 4), rowSpacing=2, columnWidth=280)
            pm.separator(h=10)
            pm.text("--- Import Bundang Apart ---", h=23)
            pm.button(l="A", c=lambda x: self.importAPT("A"))
            pm.button(l="B", c=lambda x: self.importAPT("B"))
            pm.button(l="C", c=lambda x: self.importAPT("C"))
            pm.button(l="D", c=lambda x: self.importAPT("D"))
            pm.button(l="E", c=lambda x: self.importAPT("E"))
            pm.button(l="F", c=lambda x: self.importAPT("F"))
            pm.button(l="G", c=lambda x: self.importAPT("G"))
            pm.separator(h=10)
            self.ratio = pm.floatFieldGrp(l='Ratio : ', nf=1, v1=1)
            pm.button(l='Delete Keys', c=lambda x: self.defaultSetting())
            pm.button(l='Build Up', c=lambda x: self.buildUp())
            pm.button(l='Select Groups', c=lambda x: self.selectGroup())
            pm.separator(h=10)
            pm.showWindow(win)

    # is group or not
    def isGrp(self):
        sel = pm.ls(sl=True, dag=True, type=['transform'])
        grp = []
        for i in sel:
            A = pm.listRelatives(i, s=True)
            B = pm.ls(i, type='joint')
            C = pm.ls(i, type='parentConstraint')
            if not (A or B or C):
                grp.append(i)
            else:
                continue
        return grp


    def selectGroup(self):
        grp = self.isGrp()
        grpKey = [i for i in grp if pm.keyframe(i, q=True, at="visibility", s=False, kc=True)]
        if not grpKey:
            om.MGlobal.displayError("There are no keys.")
        pm.select(grpKey)


    def getNamespace(self, obj):
        namespace = obj.rsplit(":", 1)[0] + ":" if ":" in obj else ''
        return namespace


    def getStartFrame(self, obj):
        channelName = "StartFrame"
        channelCheck = pm.attributeQuery(channelName, node=obj, ex=True) # ex = exist
        result = pm.getAttr("%s.%s" % (obj, channelName)) if channelCheck else False
        return result


    def deleteGroupKey(self, namespace, Hash):
        for i in Hash:
            grp = namespace + i + "_grp"
            pm.cutKey(grp, at="visibility", cl=True)

        
    def insertKeyToGrp(self, namespace, startFrame, Hash):
        ratio = pm.floatFieldGrp(self.ratio, q=True, v1=True)
        for i in Hash:
            grp = namespace + i + "_grp"
            key = Hash[i]
            for j, k in enumerate(key):
                frame = startFrame + k * ratio
                pm.setKeyframe(grp, at="visibility", t=frame, v=j%2, s=False)
            pm.selectKey(grp, at="visibility", s=False)
            pm.keyTangent(grp, ott="step")
            pm.selectKey(grp, at="visibility", s=False, cl=True)


    def setVisibility(self, namespace, Hash):
        for i in Hash:
            grp = namespace + i + "_grp"
            num = 1 if "wall" in i or "roof" in i else 0
            pm.setAttr(grp + ".visibility", num)


    def getHashType(self, namespace):
        parsingNamespace = namespace.split("_")
        if "bundangmainA" in parsingNamespace:
            result = self.bundangmainA
        elif "bundangmainB" in parsingNamespace:
            result = self.bundangmainB
        elif "bundangmainC" in parsingNamespace:
            result = self.bundangmainC
        elif "bundangmainD" in parsingNamespace:
            result = self.bundangmainD
        elif "bundangmainE" in parsingNamespace:
            result = self.bundangmainE
        elif "bundangmainF" in parsingNamespace:
            result = self.bundangmainF
        else:
            result = False
        return result


    def defaultSetting(self):
        sel = pm.ls(sl=True)
        for i in sel:
            namespace = self.getNamespace(i)
            Hash = self.getHashType(namespace)
            if not Hash:
                continue
            else:
                self.deleteGroupKey(namespace, Hash)
                self.setVisibility(namespace, Hash)


    def buildUp(self):
        sel = pm.ls(sl=True)
        for i in sel:
            namespace = self.getNamespace(i)
            startFrame = self.getStartFrame(i)
            Hash = self.getHashType(namespace)
            if not Hash:
                continue
            else:
                self.insertKeyToGrp(namespace, startFrame, Hash)


    def importAPT(self, typ):
        APT = f"Y:/SON/Assets/Env/bundangmain{typ}/rig/pub/scenes/env_bundangmain{typ}_rig_v9999.ma"
        if not os.path.isfile(APT):
            om.MGlobal.displayError("There is no Apartment.")
        else:
            namespace = self.getVersion(typ)
            if namespace:
                name = namespace
            else:
                APTbase = os.path.basename(APT)
                name, ext = os.path.splitext(APTbase)
            pm.createReference(APT, r=True, typ='mayaAscii', iv=True, gl=True, mnc=True, op='v=0', ns=name)
    

    def getVersion(self, typ):
        keyword1 = f"env_bundangmain{typ}_rig"
        keyword2 = "mdl"
        refList = pm.ls(rf=True)
        namespaceList = [pm.referenceQuery(i, ns=True) for i in refList]
        conditionList = [i for i in namespaceList if keyword1 in i and not keyword2 in i]
        verList = []
        for i in conditionList:
            ver = i.split("_")[-1]
            ver = int(ver[1:])
            verList.append(ver)
        if verList:
            verList.sort()
            max = verList[-1]
            namespace = f"{keyword1}_v{max + 1}"
        else:
            namespace = False
        return namespace


bundangmain()