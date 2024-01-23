import maya.standalone
import maya.cmds as cmds
import pymel.core as pm
from math import *
import maya.OpenMaya as OpenMaya
import pymel.core.datatypes as dt
import numpy as np


def standalone_template():
    # Start in batch mode
    maya.standalone.initialize(name='python')
 
    cmds.file("C:/Users/hjk03/Desktop/a.ma", f=True, o=True)
    print(cmds.ls(dag=True, s=True))
 
    # Do your magic here
 
    # Save it
    # cmds.file(s=True, f=True)


def createChannels():
    sel = pm.ls(sl=True)
    channelList = [
        "Toe", 
        "Bank", 
        "Twist", 
        "Heel", 
        "Ball", 
        "Down", 
        ]
    # channelList = [
    #     "FKIK_L_F", 
    #     "FKIK_R_F", 
    #     "FKIK_L_B", 
    #     "FKIK_R_B", 
    #     ]
    for i in sel:
        for cName in channelList:
            pm.addAttr(i, ln=cName, at='double', dv=0)
            pm.setAttr(f'{i}.{cName}', e=True, k=True)


def connectBlendColors():
    sel = pm.ls(sl=True)
    tmp = int(len(sel) / 3)
    IK = [sel[i] for i in range(tmp)]
    FK = [sel[i] for i in range(tmp, (tmp*2))]
    FBX = [sel[i] for i in range((tmp*2), (tmp*3))]
    SWITCH = "cc_global.FKIK_Tail"
    setR = pm.shadingNode("setRange", au=True)
    pm.connectAttr(SWITCH, f"{setR}.valueX", f=True)
    for i in range(tmp):
        createBlendColors(SWITCH, setR, IK[i], FK[i], FBX[i])


def createBlendColors(SWITCH, setR, IK, FK, FBX):
    bls = pm.shadingNode("blendColors", au=True)
    pm.connectAttr(f"{FK}.rotate", f"{bls}.color1", f=True)
    pm.connectAttr(f"{IK}.rotate", f"{bls}.color2", f=True)
    pm.connectAttr(f"{bls}.output", f"{FBX}.rotate", f=True)
    pm.setAttr(f"{setR}.oldMaxX", 10)
    pm.setAttr(f"{setR}.maxX", 1)
    pm.connectAttr(f"{setR}.outValueX", f"{bls}.blender", f=True)


def getDistance(sp: list, ep: list):
    x1, y1, z1 = sp
    x2, y2, z2 = ep
    result = sqrt(pow(x1-x2, 2) + pow(y1-y2, 2) + pow(z1-z2, 2))
    result = round(result, 3)
    return result


# Point position to create a controller
def pointPosition():
    sel = pm.ls(sl=True, fl=True)
    pos = [pm.pointPosition(i) for i in sel]
    point = [tuple([round(j, 3) for j in i]) for i in pos]
    print(point)
    return point


def createBones():
    sel = pm.ls(sl=True)
    for i in sel:
        pm.select(d=True)
        jnt = pm.joint(p=(0,0,0), rad=3)
        pm.matchTransform(jnt, i, pos=True)


def parentBone():
    sel = pm.ls(sl=True)
    for j, k in enumerate(sel):
        if (j + 1) < len(sel):
            pm.parent(sel[j+1], k)
        else:
            continue


def createLocatorsNormalDirection():
    selections = pm.ls(sl=True, fl=True)
    for i in selections:
        vertexPosition = pm.pointPosition(i)
        normalPosition = pm.polyNormalPerVertex(i, q=True, normalXYZ=True)[0:3]
        locator = pm.spaceLocator(p=(0,0,0))
        rotationMatrix = pm.datatypes.Matrix(pm.dt.Vector(normalPosition).normal())
        pm.xform(locator, matrix=rotationMatrix)
        pm.move(locator, vertexPosition)


def getCurvesVertexPosition(toINT=0):
    sel = pm.selected(sl=True, fl=True)
    result = []
    for i in sel:
        x, y, z = pm.pointPosition(i)
        if toINT:
            x = int(x)
            y = int(y)
            z = int(z)
        else:
            x = round(x, 3)
            y = round(y, 3)
            z = round(z, 3)
        result.append((x, y, z))
    print(result)


# 79 char line ================================================================
# 72 docstring or comments line ========================================


class ChangeRotateOrderPreserveKey:
    def __init__(self):
        """ Change rotation order while maintaining key.
        The string arguments must be as follows
        - "xyz", "yzx", "zxy", "xzy", "yxz", "zyx" \n
        >>> cro = ChangeRotateOrderPreserveKey()
        >>> cro.switchRotateOrder("yzx")
         """
        self.rotateOrders = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]


    def switchRotateOrder(self, inputOrder: str) -> None:
        try:
            rotationOrdersIndex = self.rotateOrders.index(inputOrder)
        except:
            return
        selections = pm.ls(sl=True, typ="transform")
        for obj in selections:
            rotationNodes = self.getConnectedRotationNodes(obj)
            animCurves = filter(self.isAnimCurve, rotationNodes)
            frames = self.getKeyFramesAnimCurves(animCurves)
            objectForCopy = obj.duplicate()[0]
            objectForPaste = obj.duplicate()[0] 
            objectForCopy.rotateOrder.set(rotationOrdersIndex) 
            objectForPaste.rotateOrder.set(rotationOrdersIndex)
            pm.orientConstraint(obj, objectForCopy)
            self.copyRotationKey(objectForCopy, objectForPaste, frames)
            pm.delete(objectForCopy)  
            obj.rotateOrder.set(rotationOrdersIndex)
            self.copyRotationKey(objectForPaste, obj, frames)
            pm.delete(objectForPaste)


    def getConnectedRotationNodes(self, object: pm.PyNode) -> list:
        connectedRotateX = object.rx.listConnections(d=False)
        connectedRotateY = object.ry.listConnections(d=False)
        connectedRotateZ = object.rz.listConnections(d=False)
        result = connectedRotateX + connectedRotateY + connectedRotateZ
        return result


    def isAnimCurve(self, selection: pm.PyNode) -> bool:
        isTA = type(selection) == pm.nt.AnimCurveTA
        isTL = type(selection) == pm.nt.AnimCurveTL
        isTU = type(selection) == pm.nt.AnimCurveTU
        if isTA or isTL or isTU:
            return True
        else:
            return False


    def getKeyFramesAnimCurves(self, animCurves: list) -> list:
            frames = []                            
            for i in animCurves:
                for key in range(0, i.numKeys()): 
                    frame = i.getTime(key)
                    if frame not in frames:
                        frames.append(frame)
            return frames


    def copyRotationKey(self, sourceObj, pasteObj, frames) -> None:
        for frame in frames:
            pm.currentTime(frame)
            rotation = sourceObj.r.get()
            pasteObj.r.set(rotation)
            pm.setKeyframe(pasteObj.r)


class Align:
    def __init__(self):
        pass


    def lineUp(self, threePoints=[]):
        """ In 3D space, Three points make a face, 
        The remaining objects are located on this plane.
         """
        sel = self.isThreePoints(threePoints)
        if not sel:
            return
        point3 = sel[:3]
        leftPoints = sel[3:]
        point3Position = [pm.xform(i, q=1, t=1, ws=1) for i in point3]
        normalVector = self.getFaceNormalVector(point3Position)
        planePoint = point3Position[0]
        for i in leftPoints:
            pointOfLine = pm.xform(i, q=True, t=True, ws=True)
            intersectionPoint = self.getIntersectionPoint(normalVector, \
                                planePoint, normalVector, pointOfLine)
            pm.move(i, intersectionPoint)


    def isThreePoints(self, threePoints=[]):
        point3 = threePoints if threePoints else pm.ls(sl=True)
        if len(point3) < 3:
            return
        else:
            return point3


    def getFaceNormalVector(self, threePointsPosition=[]):
        """ Given three points, 
        create a face and return the normal vector of the face.
        """
        face = pm.polyCreateFacet(p=threePointsPosition)
        info = pm.polyInfo(face, fn=True)
        stripInfo = info[0].split(":")[-1].strip()
        normalVector = [float(i) for i in stripInfo.split(" ")]
        return normalVector


    def getIntersectionPoint(self, normalOfPlane: list, pointOnPlane: list, \
            directionOfLine: list, pointOnLine: list) -> list:
        """ Get intersection of plane and line.
        - Equation of surface: dot(normalOfPlane, X - pointOfPlane) = 0
        - Equation of line: pointOfLine + lean*directionOfLine
        """
        planeNormal = np.array(normalOfPlane)
        planePoint = np.array(pointOnPlane)
        lineDirection = np.array(directionOfLine)
        linePoint = np.array(pointOnLine)
        delta1 = np.dot(planeNormal, (planePoint - linePoint)) 
        delta2 = np.dot(planeNormal, lineDirection)
        lean = delta1 / delta2
        intersectionPoint = pointOnLine + (lean*lineDirection)
        return intersectionPoint.tolist()


