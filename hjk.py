import re
import os
import json
import shutil
import math
import sympy
import functools
import maya.OpenMaya as om
import pymel.core as pm
import maya.mel as mel


class SoftSel:
    def __init__(self):
        """ Get this code from internet. Modified to class. """
        self.createSoftCluster()
    
    
    def softSelection(self):
        selection = om.MSelectionList()
        softSelection = om.MRichSelection()
        om.MGlobal.getRichSelection(softSelection)
        softSelection.getSelection(selection)
        dagPath = om.MDagPath()
        component = om.MObject()
        iter = om.MItSelectionList(selection, om.MFn.kMeshVertComponent)
        elements = []
        while not iter.isDone(): 
            iter.getDagPath(dagPath, component)
            dagPath.pop()
            node = dagPath.fullPathName()
            fnComp = om.MFnSingleIndexedComponent(component)   
            for i in range(fnComp.elementCount()):
                elem = fnComp.element(i)
                infl = fnComp.weight(i).influence()
                elements.append([node, elem, infl])
            iter.next()
        return elements
        
    
    def createSoftCluster(self):
        softElementData = self.softSelection()
        selection = ["%s.vtx[%d]" % (el[0], el[1]) for el in softElementData] 
        pm.select(selection, r=True)
        cluster = pm.cluster(relative=True)
        for i in range(len(softElementData)):
            pm.percent(cluster[0], selection[i], v=softElementData[i][2])
        pm.select(cluster[1], r=True)


class Han:
    def __init__(self):
        """ Transform HanGeul unicode to bytes. Otherside too. """
        self.btnHan1 = b'\xec\x9d\xb8\xec\xbd\x94\xeb\x94\xa9'
        self.btnHan2 = b'\xec\xa7\x80\xec\x9a\xb0\xea\xb8\xb0'
        self.HanGeul = b'\xed\x95\x9c\xea\xb8\x80'
        self.setupUI()


    # UI.
    def setupUI(self):
        if pm.window('HanGeul', exists=True):
            pm.deleteUI('HanGeul')
        else:
            win = pm.window('HanGeul', t='Encode / Decode', s=True, rtf=True)
            pm.columnLayout(cat=('both', 4), rowSpacing=2, columnWidth=240)
            pm.separator(h=10)
            self.hanField = pm.textField(ed=True, pht=self.HanGeul)
            self.utfField = pm.textField(ed=True, pht="Bytes")
            self.btn = pm.button(l=self.btnHan1, c=lambda x: self.transform())
            pm.separator(h=10)
            pm.showWindow(win)


    # The field value is returned as a string type.
    def transform(self):
        A = self.hanField.getText()
        B = self.utfField.getText()
        if A and not B:
            result = r"%s" % (str(A).encode("utf-8"))
            self.utfField.setText(result)
            self.btn.setLabel(self.btnHan2)
        elif B and not A:
            result = eval(B)
            self.hanField.setText(result.decode("utf-8", "strict"))
            self.btn.setLabel(self.btnHan2)
        else:
            self.hanField.setText("")
            self.utfField.setText("")
            self.btn.setLabel(self.btnHan1)


class AutoWheel_Rig:
    def __init__(self):
        """ Create wheels that rotate automatically """
        self.main()
    

    def main(self):
        sel = pm.ls(sl=True)
        if not sel:
            om.MGlobal.displayError('Nothing selected.')
        else:
            for i in sel:
                rad = self.createRad(i)
                var = self.createVar(rad)
                self.createRig(i, var, rad)
    

    # Return obj's radius.
    def createRad(self, obj: str) -> float:
        # bb: bounding box
        bbObj = pm.xform(obj, q=True, bb=True)
        xMin, yMin, zMin, xMax, yMax, zMax = bbObj
        x = (xMax - xMin) / 2
        y = (yMax - yMin) / 2
        z = (zMax - zMin) / 2
        bbList = [x, y, z]
        bbList.sort(reverse=True) # biggest
        bb = bbList[0] # 0.12345678
        result = round(bb, 3) # 0.123
        return result


    # Create variables.
    def createVar(self, rad: float) -> tuple:
        rad *= 1.2
        cuv = pm.circle(nr=(1,0,0), r=rad, ch=False, n='cc_wheel_L_Bk')
        cuv = cuv[0]
        jnt = cuv + '_jnt'
        null = cuv + '_null_grp'
        prev = cuv + '_prev_grp'
        orient = cuv + '_orient_Grp'
        br = '\n'
        # expression1 ==================================================
        expr1 = f'float $R = {cuv}.Radius;{br}'
        expr1 += f'float $A = {cuv}.AutoRoll;{br}'
        expr1 += f'float $J = {jnt}.rotateX;{br}'
        expr1 += f'float $C = 2 * 3.141 * $R;{br}' # 2*pi*r
        expr1 += f'float $O = {orient}.rotateY;{br}'
        expr1 += f'float $S = 1;{br}' # Connect the global scale.
        expr1 += f'float $pX = {cuv}.PrevPosX;{br}'
        expr1 += f'float $pY = {cuv}.PrevPosY;{br}'
        expr1 += f'float $pZ = {cuv}.PrevPosZ;{br}'
        expr1 += f'{prev}.translateX = $pX;{br}'
        expr1 += f'{prev}.translateY = $pY;{br}'
        expr1 += f'{prev}.translateZ = $pZ;{br}'
        expr1 += f'float $nX = {cuv}.translateX;{br}'
        expr1 += f'float $nY = {cuv}.translateY;{br}'
        expr1 += f'float $nZ = {cuv}.translateZ;{br*2}'
        # expression2: Distance between two points.
        expr2 = f'float $D = `mag<<$nX-$pX, $nY-$pY, $nZ-$pZ>>`;{br*2}'
        # expression3: Insert value into jonit rotation.
        expr3 = f'{jnt}.rotateX = $J' # Original rotation value.
        expr3 += ' + ($D/$C) * 360' # Proportional: (d / 2*pi*r) * 360
        expr3 += ' * $A' # Auto roll switch.
        expr3 += ' * 1' # Create other switches.
        expr3 += ' * sin(deg_to_rad($O))' # When the wheel turns.
        expr3 += f' / $S;{br*2}' # Resizing the global scale.
        # expression4
        expr4 = f'{cuv}.PrevPosX = $nX;{br}'
        expr4 += f'{cuv}.PrevPosY = $nY;{br}'
        expr4 += f'{cuv}.PrevPosZ = $nZ;{br}'
        # expression Final =============================================
        exprFinal = expr1 + expr2 + expr3 + expr4
        # Result
        result = (cuv, jnt, null, prev, orient, exprFinal)
        return result


    # Construct a rig inside maya.
    def createRig(self, obj: str, var: tuple, rad: float) -> None:
        # variables
        cuv, jnt, null, prev, orient, expr = var
        # channel to cuv
        pm.addAttr(cuv, ln='Radius', at='double', dv=1)
        pm.setAttr(f'{cuv}.Radius', e=True, k=True)
        pm.setAttr(f'{cuv}.Radius', rad)
        pm.addAttr(cuv, ln='AutoRoll', at='long', min=0, max=1, dv=1)
        pm.setAttr(f'{cuv}.AutoRoll', e=True, k=True)
        for i in ['X', 'Y', 'Z']:
            pm.addAttr(cuv, ln=f'PrevPos{i}', at='double', dv=0)
            pm.setAttr(f'{cuv}.PrevPos{i}', e=True, k=True)
        # create joint inside cuv
        pm.joint(n=jnt, p=(0,0,0))
        # create groups
        pm.group(n=null, em=True, p=cuv)
        pm.group(n=prev, em=True, w=True)
        pm.group(n=orient, em=True, p=prev)
        grp = pm.group(cuv, prev)
        pm.matchTransform(grp, obj, pos=True)
        # create constraints
        pm.aimConstraint(cuv, prev, mo=False)
        pm.orientConstraint(null, orient, mo=False)
        pm.expression(s=expr, o='', ae=1, uc='all')


class AutoWheel_Key:
    def __init__(self):
        """ Set the key on the wheel to turn automatically. """
        self.Min = pm.playbackOptions(q=True, min=True)
        self.Max = pm.playbackOptions(q=True, max=True)
        self.setupUI()


    def setupUI(self):
        if pm.window('AutoWheel2', exists=True):
            pm.deleteUI('AutoWheel2')
        else:
            title = "Set the key on the wheel to turn automatically."
            win = pm.window('AutoWheel2', t=title, s=True, rtf=True)
            pm.columnLayout(cat=('both', 4), rowSpacing=2, columnWidth=210)
            pm.separator(h=10)
            pm.rowColumnLayout(nc=4, cw=[(1, 55), (2, 50), (3, 15), (4, 50)])
            pm.text("Frame : ")
            self.startF = pm.intField("startFrame", ed=True, v=self.Min)
            pm.text(" - ")
            self.endF = pm.intField("endFrame", v=self.Max)
            pm.setParent("..", u=True)
            pm.button(l='Auto Rotation', c=lambda x: self.main())
            pm.button(l='Delete Key', c=lambda x: self.deleteKey())
            pm.separator(h=10)
            pm.showWindow(win)
    

    def main(self):
        sel = pm.ls(sl=True)
        radiusCheck = []
        for i in sel:
            attrCheck = pm.attributeQuery('Radius', node=i, ex=True)
            if not attrCheck:
                radiusCheck.append(i)
        if not sel:
            print("Nothing Selected.")
        elif radiusCheck:
            print("The controller does not have a radius attribute.")
        else:
            for i in sel:
                self.autoRotate(i)


    def autoRotate(self, obj):
        startFrame = self.startF.getValue()
        endFrame = self.endF.getValue()
        rad = pm.getAttr(f"{obj}.Radius")
        size = pm.xform(obj, q=True, s=True, ws=True)
        size = max(size)
        pointList = {}
        for i in range(startFrame, endFrame + 1):
            pm.currentTime(i)
            pm.setKeyframe(at="rotateX")
            pos = pm.xform(obj, q=True, ws=True, rp=True)
            pos = [round(j, 3) for j in pos]
            pointList[i] = pos
            if len(pointList) < 2:
                continue
            else:
                x1, y1, z1 = pointList[i - 1]
                x2, y2, z2 = pointList[i]
                dx = x2 - x1
                dy = y2 - y1
                dz = z2 - z1
                d = math.sqrt(pow(dx, 2) + pow(dy, 2) + pow(dz, 2))
                d = round(d, 3)
                pm.currentTime(i - 1)
                angle = pm.getAttr(f"{obj}.rotateX")
                angle += d * 360 / (2 * 3.14159 * rad * size)
                pm.currentTime(i)
                pm.setKeyframe(obj, v=angle, at="rotateX")


    def deleteKey(self):
        sel = pm.ls(sl=True)
        startFrame = self.startF.getValue()
        endFrame = self.endF.getValue()
        for i in sel:
            pm.cutKey(i, cl=True, at="rx", t=(startFrame, endFrame))
        

class MatchPivot:
    def __init__(self):
        """ Matching the direction of the pivot using 3points. """
        self.main()


    # Check if selected is a point.
    def check(self, sel: list) -> bool:
        vtxList = [i for i in sel if isinstance(i, pm.MeshVertex)]
        if not sel:
            om.MGlobal.displayError('Nothing selected.')
            result = False
        elif len(sel) != 3 or len(vtxList) != 3:
            om.MGlobal.displayError('Select 3 points.')
            result = False
        else:
            result = True
        return result


    # Decide the direction.
    # Input is a list of 3 points.
    def select3Points(self, sel: list) -> str:
        # shp: shape
        shp = sel[0].split('.')[0]
        # Object's name
        obj = pm.listRelatives(shp, p=True)
        obj = obj[0]
        # pPlane's name
        pPlane = pm.polyPlane(sx=1, sy=1, ax=(0, 1, 0), cuv=2, ch=False)
        pPlane = pPlane[0]
        vtx = pm.ls(f"{pPlane}.vtx[0:2]", fl=True)
        all = vtx + sel
        pm.select(all)
        mel.eval("snap3PointsTo3Points(0);")
        pm.select(cl=True)
        return pPlane

    
    def main(self) -> None:
        sel = pm.ls(sl=True, fl=True)
        chk = self.check(sel)
        if not chk:
            pass
        else:
            obj = self.select3Points(sel)
            loc = pm.spaceLocator()
            pm.matchTransform(loc, obj, pos=True, rot=True)
            pm.delete(obj)


class MatchCuvShp:
    def __init__(self):
        """ Match the curve shape from A to B.
        Select only nurbsCurves. """
        self.main()


    # Number of Object's cv.
    def numberOfCV(self, obj: str) -> int:
        cv = f'{obj}.cv[0:]'
        pm.select(cv)
        cvSel = pm.ls(sl=True, fl=True)
        cvNum = len(cvSel)
        result = cvNum
        pm.select(cl=True)
        return result

        
    # Match the point to point.
    # Change the shape of the curve controller from A to B
    def matchShape(self, obj: list) -> list:
        A_list = obj[0:-1]
        B = obj[-1] # The last selection is Base.
        numB = self.numberOfCV(B) # number of B.cv
        failed = []
        for A in A_list:
            numA = self.numberOfCV(A)
            if numA == numB > 0:
                for k in range(numA):
                    cvA = f'{A}.cv[{k}]'
                    cvB = f'{B}.cv[{k}]'
                    p1, p2, p3 = pm.pointPosition(cvB)
                    pm.move(p1, p2, p3, cvA, a=True)
            else:
                failed.append(A)
        return failed


    # Select at least 2.
    def main(self):
        sel = pm.ls(sl=True, dag=True, type=['nurbsCurve'])
        if len(sel) < 2:
            print('Select two or more "nurbsCurves".')
        else:
            result = self.matchShape(sel)
            failed = 'Check this objects : %s' % result
            success = 'Successfully done.'
            message = failed if result else success
            print(message)


class MirrorCopy:
    def __init__(self, **kwargs):
        """ Parameter can be (x=True or z=True).
        First Select groups.
        Copy the group and mirror it in the direction. 
        If there is a curve in it, copy the curve and mirror it.
         """
        if not kwargs:
            print("Parameter is required. ex) x=True or z=True")
            return
        keys = [i for i in kwargs.keys() if i == ('x' or 'z')]
        keys = [i for i in keys if kwargs[i]]
        if not keys:
            print("None of the parameters are True.")
        else:
            self.key = keys[0]
            self.val = kwargs[self.key]
            self.sel = pm.ls(sl=True)
            self.main()


    # Check the conditions.
    def main(self):
        if not self.sel:
            print("Nothing selected.")
            return
        for i in self.sel:
            self.mirrorCopy(i)


    # If there is a curve in the group, copy the curve and mirror it.
    def mirrorCopy(self, selection):
        cuv = selection.getChildren()
        shp = pm.ls(cuv, dag=True, s=True)
        typ = 'nurbsCurve'
        objs = {i.getParent().name() for i in shp if pm.objectType(i)==typ}
        objs = list(objs)
        if not objs:
            self.mirrorGroup(selection)
        else:
            for obj in objs:
                name = self.swapLR(obj)
                copy = pm.duplicate(obj, rr=True, n=name)
                pm.parent(copy, w=True)
                grp = pm.group(em=True)
                pm.parent(copy, grp)
                direction = [-1, 1, 1] if self.key=='x' else [1, 1, -1]
                pm.scale(grp, direction, r=True)
                mirrorGrp = self.mirrorGroup(selection)
                pm.parent(copy, mirrorGrp)
                pm.makeIdentity(copy, a=True, t=1, r=1, s=1, n=0, pn=1)
                pm.delete(grp)
        

    # Replace letter L with R
    def swapLR(self, objName):
        if '_L' in objName:
            result = objName.replace('_L', '_R')
        elif '_R' in objName:
            result = objName.replace('_R', '_L')
        else:
            result = ''
        return result


    # Create a mirrored group.
    def mirrorGroup(self, selection):
        name = self.swapLR(selection.name())
        grp = pm.group(em=True, n=name)
        pm.matchTransform(grp, selection, pos=True, rot=True)
        tra = pm.getAttr(f'{grp}.translate')
        rot = pm.getAttr(f'{grp}.rotate')
        tx, ty, tz = tra
        rx, ry, rz = rot
        if self.key == 'x':
            tx *= -1
            rx += (180 if rx < 0 else -180)
            ry *= -1
            rz *= -1
        else:
            tz *= -1
            rz += (180 if rz < 0 else -180)
        attr = {'tx': tx, 'ty': ty, 'tz': tz, 'rx': rx, 'ry': ry, 'rz': rz}
        for j, k in attr.items():
            pm.setAttr(f'{grp}.{j}', k)
        return grp


class VertexSeletor:
    def __init__(self):
        """ Save the selected vertices, lines and faces, 
        to json files in the same path of this scene.
         """
        self.jsonPath = self.getJsonPath()
        if not self.jsonPath:
            return
        else:
            self.setupUI()
    

    def getJsonPath(self):
        """ Create the path of the json file based on this scene. """
        fullPath = pm.Env().sceneName()
        if not fullPath:
            print("File not saved.")
            return
        else:
            dir = os.path.dirname(fullPath)
            # name_ext = os.path.basename(fullPath)
            # name, ext = os.path.splitext(name_ext)
            result = f"{dir}/vertexSeletor.json"
            return result

    # UI
    def setupUI(self):
        winName = 'vertexButton'
        if pm.window(winName, exists=True):
            pm.deleteUI(winName)
        else:
            win = pm.window(winName, t='Vertex Selector', s=True, rtf=True)
            pm.columnLayout(cat=('both', 4), rs=2, cw=178)
            pm.separator(h=10)
            pm.rowColumnLayout(nc=3, cw=[(1, 80), (2, 5), (3, 80)])
            self.field = pm.textField(ed=True)
            pm.text('')
            pm.button(l="Create", c=lambda x: self.writeJson())
            pm.setParent("..", u=True)
            pm.separator(h=10)
            pm.rowColumnLayout(nc=3, cw=[(1, 80), (2, 5), (3, 80)])
            pm.radioCollection()
            self.radioAdd = pm.radioButton(l='add', sl=True)
            pm.text('')
            self.radioTgl = pm.radioButton(l='tgl')
            pm.setParent("..", u=True)
            spacing = [(1, 80), (2, 3), (3, 80), (4, 3)]
            pm.rowColumnLayout(nc=4, rs=(1, 3), cw=spacing)
            chk = os.path.isfile(self.jsonPath)
            if chk:
                data = self.loadJson()
                for key in data:
                    self.button(key)
            else:
                pass
            pm.setParent("..", u=True)
            pm.separator(h=10)
            pm.button(l="Clear", c=lambda x: pm.select(cl=True))
            pm.button(l="Delete Data", c=lambda x: self.deleteJson())
            pm.button(l="Close", c=lambda x: pm.deleteUI(winName))
            pm.separator(h=10)
            pm.showWindow(win)


    def button(self, *args):
        """ Create the looping button. """
        for i in args:
            pm.button(l=i, c=lambda x: self.selectVtx(i))
            pm.text(' ')


    def writeJson(self) -> None:
        """ If the json file does not exist, create a new one.
        Otherwise, Save the dictionary as a json file
         """
        chk = os.path.isfile(self.jsonPath)
        if not chk:
            data = {}
        else:
            data = self.loadJson()
        name = self.field.getText()
        info = self.vertexNum()
        data[name] = info
        with open(self.jsonPath, 'w') as JSON:
            json.dump(data, JSON, indent=4)


    def loadJson(self) -> dict:
        """ Load information from json file and select vertex. """
        with open(self.jsonPath, 'r') as JSON:
            data = json.load(JSON)
        return data


    def deleteJson(self):
        """ It doesn't delete the data, it destroys the file itself. """
        chk = os.path.isfile(self.jsonPath)
        if not chk:
            return
        else:
            os.remove(self.jsonPath)


    def vertexNum(self) -> dict:
        """ Make a list of vertex numbers only. """
        sel = pm.ls(sl=True)
        obj = pm.ls(sel, o=True)
        shapes = set(obj)
        result = {}
        for shp in shapes:
            com = re.compile(f'(?<={shp}).+[0-9]+:*[0-9]*.+')
            vtxNum = []
            for j in sel:
                try:
                    tmp = com.search(j.name())
                    vtxNum.append(tmp.group(0))
                except:
                    continue
            result[shp.getParent().name()] = vtxNum
        return result


    def selectVtx(self, key: str):
        """ Click the button, selects the vortex. """
        data = self.loadJson()
        temp = data[key]
        result = []
        for j, k in temp.items():
            for i in k:
                result.append(j + i)
        ADD = self.radioAdd.getSelect()
        TGL = self.radioTgl.getSelect()
        pm.select(result, af=ADD, tgl=TGL)


class LineConnect:
    def __init__(self):
        """ Creates a line connecting two objects or two points.
        If you select a point initially, 
        the last one you select must also be a point. 
        If you have selected an object, you must select the object last.
        input() is where you put the name of the line..
         """
        self.sel = pm.ls(sl=True, fl=True)
        try:
            self.name = input()
        except:
            print("Cancled.")
            return
        self.main()


    def main(self):
        """ Make a line first. 
        Create an expression that calculates the distance between two points, 
        and create a channel to write it. 
        Connect each with pointConstraint and aimConstraint. 
        upVector is used for aimConstraint.
         """
        if not self.sel:
            print("Nothing selected.")
        elif len(self.sel) < 2:
            print("Two points are needed.")
        else:
            # cuv: curve
            # cuvLen: length of curve
            # aloc: start object or point
            # oloc: last object or point
            # grp: group of curve
            # upV: up vector of the curve
            cuv, aloc, oloc = self.makeLine()
            cuvLen = pm.arclen(cuv)
            cuvLen = round(cuvLen, 3)
            self.makeAttr(cuv)
            self.makeExression(aloc, oloc, cuv, cuvLen)
            grp = self.makeGroup(cuv)
            upV = self.makeUpVector(cuv, grp)
            self.makeConstraint(aloc, oloc, cuv, upV)


    # Create a line connecting two points.
    def makeLine(self) -> str:
        alpha = self.sel[0]
        omega = self.sel[-1]
        try:
            aPos, oPos = [pm.pointPosition(i) for i in [alpha, omega]]
        except:
            tmp = []
            for i in [alpha, omega]:
                pos = pm.xform(i, q=1, ws=1, rp=1)
                tmp.append(pos)
            aPos, oPos = tmp
        cuv = pm.curve(d=1, p=[aPos, oPos], n=self.name)
        sPiv = f"{cuv}.scalePivot"
        rPiv = f"{cuv}.rotatePivot"
        aLoc = pm.spaceLocator(n=f"{cuv}_startLoc")
        oLoc = pm.spaceLocator(n=f"{cuv}_endLoc")
        a1, a2, a3 = aPos
        o1, o2, o3 = oPos
        pm.move(a1, a2, a3, aLoc, r=True)
        pm.move(o1, o2, o3, oLoc, r=True)
        pm.move(a1, a2, a3, sPiv, rPiv, rpr=True)
        pm.aimConstraint(oLoc, aLoc)
        pm.delete(aLoc, cn=True)
        pm.parent(cuv, aLoc)
        pm.makeIdentity(cuv, a=True, t=1, r=1, s=1, n=0, pn=1)
        pm.parent(cuv, w=True)
        pm.rebuildCurve(cuv, d=1, ch=0, s=3, rpo=1, end=1, kr=0, kt=0)
        pm.xform(cuv, cpc=True)
        return cuv, aLoc, oLoc


    # create attr to curve
    def makeAttr(self, cuv):
        for attrName in ['Distance', 'Ratio']:
            pm.addAttr(cuv, ln=attrName, at='double', dv=0)
            pm.setAttr(f'{cuv}.{attrName}', e=True, k=True)


    # create expression to curve attr
    def makeExression(self, Loc1, Loc2, cuv, cuvLen):
        BR = "\n"
        expr = f"float $uX = {Loc1}.translateX;" + BR
        expr += f"float $uY = {Loc1}.translateY;" + BR
        expr += f"float $uZ = {Loc1}.translateZ;" + BR
        expr += f"float $dX = {Loc2}.translateX;" + BR
        expr += f"float $dY = {Loc2}.translateY;" + BR
        expr += f"float $dZ = {Loc2}.translateZ;" + BR
        expr += "float $D = `mag<<$dX-$uX, $dY-$uY, $dZ-$uZ>>`;" + BR
        expr += f"{cuv}.Distance = $D;" + BR
        expr += f"{cuv}.Ratio = $D / {cuvLen};"
        pm.expression(s=expr, o='', ae=1, uc='all')


    # create group
    def makeGroup(self, obj):
        grp = pm.group(em=True, n=f"{obj}_grp")
        pm.matchTransform(grp, obj, pos=True, rot=True)
        pm.parent(obj, grp)
        return grp


    # create upVector
    def makeUpVector(self, cuv, grp):
        locUpVector = pm.spaceLocator(n=f'{cuv}_upVector')
        length = pm.getAttr(f"{cuv}.Distance")
        pm.matchTransform(locUpVector, cuv, pos=True, rot=True)
        pm.parent(locUpVector, grp)
        pm.move(0, length, 0, locUpVector, r=True, ls=True, wd=True)
        # pm.parent(locUpVector, w=True)
        return locUpVector


    # The line is centered between the two points.
    def makeConstraint(self, Loc1, Loc2, cuv, upVector):
        up = upVector.name(long=True)
        pm.pointConstraint(Loc1, cuv, mo=True, w=0.5)
        pm.pointConstraint(Loc2, cuv, mo=True, w=0.5)
        pm.aimConstraint(Loc2, cuv, wut="object", wuo=up)
        for i in ["sx", "sy", "sz"]:
            pm.connectAttr(f"{cuv}.Ratio", f"{cuv}.{i}")


class Colors:
    def __init__(self):
        """ Change the color of the shape. """
        self.setupUI()


    # UI
    def setupUI(self):
        winName = 'colorsButton'
        if pm.window(winName, exists=True):
            pm.deleteUI(winName)
        else:
            win = pm.window(winName, t='Colors', s=True, rtf=True)
            pm.columnLayout(cat=('both', 4), rowSpacing=2, columnWidth=188)
            pm.separator(h=10)
            pm.rowColumnLayout(nc=2, cw=[(1, 90), (2, 90)])
            pm.button(l='colors_blue', c=lambda x: self.colors(blue=True))
            pm.button(l='colors_blue2', c=lambda x: self.colors(blue2=True))
            pm.button(l='colors_pink', c=lambda x: self.colors(pink=True))
            pm.button(l='colors_red', c=lambda x: self.colors(red=True))
            pm.button(l='colors_red2', c=lambda x: self.colors(red2=True))
            pm.button(l='colors_green', c=lambda x: self.colors(green=True))
            pm.button(l='colors_green2', c=lambda x: self.colors(green2=True))
            pm.button(l='colors_yellow', c=lambda x: self.colors(yellow=True))
            pm.setParent("..", u=True)
            pm.separator(h=10)
            pm.button(l="Close", c=lambda x: pm.deleteUI(winName))
            pm.separator(h=10)
            pm.showWindow(win)


    # This is Main function.
    def colors(self, **kwargs):
        sel = pm.ls(sl=True)
        colors = {
            "blue": 6, 
            "blue2": 18, 
            "pink": 9, 
            "red": 13, 
            "red2": 21, 
            "green": 14, 
            "green2": 23, 
            "yellow": 17, 
        }
        idxs = [colors[i] for i in kwargs if kwargs[i]]
        enb = 1 if idxs else 0
        idx = idxs[0] if idxs else 0
        for i in sel:
            shp = i.getShape()
            pm.setAttr(f"{shp}.overrideEnabled", enb)
            pm.setAttr(f"{shp}.overrideColor", idx)


def createCuv_thruPoint(startFrame: int, endFrame: int) -> list:
    """ Creates a curve through points.
    This function works even if you select a point.
     """
    sel = pm.ls(sl=True, fl=True)
    result = []
    for j in sel:
        pos = []
        for k in range(startFrame, endFrame + 1):
            pm.currentTime(k)
            try:
                pos.append(pm.pointPosition(j)) # vertex
            except:
                pos.append(pm.xform(j, q=1, ws=1, rp=1)) # object
        cuv = pm.curve(p=pos)
        result.append(cuv)
    return result


def createCuv_thruLoc(**kwargs) -> str:
    """ Creates a curve along the locator's points.
    Place locators first, and select them, and call this function.
    ex) cl=True -> Create a closed curve.
     """
    sel = pm.ls(sl=True) # select locators
    pos = [pm.xform(i, q=1, ws=1, rp=1) for i in sel]
    tmp = kwargs['cl'] if 'cl' in kwargs.keys() else False
    if tmp:
        cuv = pm.circle(nr=(0, 1, 0), ch=False, s=len(sel))
        cuv = cuv[0]
        for j, k in enumerate(pos):
            pm.move(k[0], k[1], k[2], f'{cuv}.cv[{j}]', ws=True)
    else:
        cuv = pm.curve(p=pos)
    return cuv


def createLoc(**kwargs):
    """ Creates locator or joint in boundingBox.
    Usage: createLoc(jnt=True) """
    sel = pm.ls(sl=True)
    for i in sel:
        bb = pm.xform(i, q=True, bb=True, ws=True)
        xMin, yMin, zMin, xMax, yMax, zMax = bb
        x = (xMin + xMax) / 2
        y = (yMin + yMax) / 2
        z = (zMin + zMax) / 2
        loc = pm.spaceLocator()
        pm.move(loc, x, y, z)
        if not kwargs:
            pass
        else:
            for key, value in kwargs.items():
                if key=="jnt" and value:
                    pm.select(cl=True)
                    jnt = pm.joint(p=(0,0,0), rad=1)
                    pm.matchTransform(jnt, loc, pos=True)
                    pm.delete(loc)
                else:
                    continue


def createLine() -> str:
    """ Create a line connecting two points. """
    sel = pm.ls(sl=True, fl=True)
    if len(sel) < 2:
        print("Two points are needed.")
    else:
        alpha = sel[0]
        omega = sel[-1]
        try:
            aPos, oPos = [pm.pointPosition(i) for i in [alpha, omega]]
        except:
            aPos, oPos = [pm.xform(i, q=1, ws=1, rp=1) for i in [alpha, omega]]
        cuv = pm.curve(d=1, p=[aPos, oPos])
        sPiv = f"{cuv}.scalePivot"
        rPiv = f"{cuv}.rotatePivot"
        aLoc = pm.spaceLocator()
        oLoc = pm.spaceLocator()
        a1, a2, a3 = aPos
        o1, o2, o3 = oPos
        pm.move(a1, a2, a3, aLoc, r=True)
        pm.move(o1, o2, o3, oLoc, r=True)
        pm.move(a1, a2, a3, sPiv, rPiv, rpr=True)
        pm.aimConstraint(oLoc, aLoc)
        pm.delete(aLoc, cn=True)
        pm.parent(cuv, aLoc)
        pm.makeIdentity(cuv, a=True, t=1, r=1, s=1, n=0, pn=1)
        pm.parent(cuv, w=True)
        pm.rebuildCurve(cuv, d=1, ch=0, s=3, rpo=1, end=1, kr=0, kt=0)
        return cuv


def createJnt_MotionPath(*arg: int) -> None:
    '''Create a number of joints and 
    apply a motionPath to the curve.
    '''
    sel = pm.ls(sl=True)
    if not sel:
        print("No curves selected.")
        return 0
    num = arg[0] if arg else int(input())
    mod = 1/(num-1) if num > 1 else 0
    cuv = sel[0]
    for i in range(num):
        pm.select(cl=True)
        jnt = pm.joint(p=(0,0,0))
        val = i * mod
        tmp = pm.pathAnimation(jnt, c=cuv, 
            fm=True, # fractionMode
            f=True, # follow
            fa='x', # followAxis
            ua='y', # upAxis
            wut='vector', # worldUpType
            wu=(0,1,0) # worldUpVector
            )
        pm.cutKey(tmp, cl=True, at='u')
        pm.setAttr(f"{tmp}.uValue", val)


def ctrl(**kwargs) -> list:
    """ Create a controller,
    "cub": cub, 
    "sph": sph, 
    "cyl": cyl, 
    "pip": pip, 
    "con": con, 
    "car": car, 
    "ar1": ar1, 
    "ar2": ar2, 
    "ar3": ar3, 
    "ar4": ar4, 
    "ar5": ar5, 
    "pointer": pointer, 
    "foot": foot, 
    "hoof": hoof, 
    "hoof2": hoof2, 
    "sqr": sqr, 
    "cross": cross, 
     """
    # Cube
    cub = [(-1, 1, -1), (-1, 1, 1), (1, 1, 1), ]
    cub += [(1, 1, -1), (-1, 1, -1), (-1, -1, -1), ]
    cub += [(-1, -1, 1), (1, -1, 1), (1, -1, -1), ]
    cub += [(-1, -1, -1), (-1, -1, 1), (-1, 1, 1), ]
    cub += [(1, 1, 1), (1, -1, 1), (1, -1, -1), ]
    cub += [(1, 1, -1), ]
    # Sphere
    sph = [(0, 1, 0), (0, 0.7, 0.7), (0, 0, 1), ]
    sph += [(0, -0.7, 0.7), (0, -1, 0), (0, -0.7, -0.7), ]
    sph += [(0, 0, -1), (0, 0.7, -0.7), (0, 1, 0), ]
    sph += [(-0.7, 0.7, 0), (-1, 0, 0), (-0.7, 0, 0.7), ]
    sph += [(0, 0, 1), (0.7, 0, 0.7), (1, 0, 0), ]
    sph += [(0.7, 0, -0.7), (0, 0, -1), (-0.7, 0, -0.7), ]
    sph += [(-1, 0, 0), (-0.7, -0.7, 0), (0, -1, 0), ]
    sph += [(0.7, -0.7, 0), (1, 0, 0), (0.7, 0.7, 0), ]
    sph += [(0, 1, 0), ]
    # Cylinder
    cyl = [(-1, 1, 0), (-0.7, 1, 0.7), (0, 1, 1), ]
    cyl += [(0.7, 1, 0.7), (1, 1, 0), (0.7, 1, -0.7), ]
    cyl += [(0, 1, -1), (0, 1, 1), (0, -1, 1), ]
    cyl += [(-0.7, -1, 0.7), (-1, -1, 0), (-0.7, -1, -0.7), ]
    cyl += [(0, -1, -1), (0.7, -1, -0.7), (1, -1, 0), ]
    cyl += [(0.7, -1, 0.7), (0, -1, 1), (0, -1, -1), ]
    cyl += [(0, 1, -1), (-0.7, 1, -0.7), (-1, 1, 0), ]
    cyl += [(1, 1, 0), (1, -1, 0), (-1, -1, 0), ]
    cyl += [(-1, 1, 0), ]
    # Pipe
    pip = [(0, 1, 1), (0, -1, 1), (0.7, -1, 0.7), ]
    pip += [(1, -1, 0), (1, 1, 0), (0.7, 1, -0.7), ]
    pip += [(0, 1, -1), (0, -1, -1), (-0.7, -1, -0.7), ]
    pip += [(-1, -1, 0), (-1, 1, 0), (-0.7, 1, 0.7), ]
    pip += [(0, 1, 1), (0.7, 1, 0.7), (1, 1, 0), ]
    pip += [(1, -1, 0), (0.7, -1, -0.7), (0, -1, -1), ]
    pip += [(0, 1, -1), (-0.7, 1, -0.7), (-1, 1, 0), ]
    pip += [(-1, -1, 0), (-0.7, -1, 0.7), (0, -1, 1), ]
    # Cone
    con = [(0, 2, 0), (-0.87, 0, -0), (0.87, 0, 0), ]
    con += [(0, 2, 0), (0, 0, 1), (-0.87, 0, -0), ]
    con += [(0.87, 0, 0), (0, 0, 1), ]
    # car
    car = [(90.878, 114.928, 109.126), (90.878, 100.171, 227.195), ]
    car += [(90.878, 29.606, 227.195), (90.878, 29.606, 113.598), ]
    car += [(90.878, 29.606, -113.598), (90.878, 29.606, -227.195), ]
    car += [(90.878, 114.928, -227.195), (90.878, 114.928, -164.271), ]
    car += [(90.878, 161.491, -102.348), (90.878, 161.491, 54.004), ]
    car += [(90.878, 114.928, 109.126), (-90.878, 114.928, 109.126), ]
    car += [(-90.878, 100.171, 227.195), (-90.878, 29.606, 227.195), ]
    car += [(-90.878, 29.606, 113.598), (-90.878, 29.606, -113.598), ]
    car += [(-90.878, 29.606, -227.195), (-90.878, 114.928, -227.195), ]
    car += [(-90.878, 114.928, -164.271), (-90.878, 161.491, -102.348), ]
    car += [(90.878, 161.491, -102.348), (90.878, 114.928, -164.271), ]
    car += [(-90.878, 114.928, -164.271), (-90.878, 114.928, -227.195), ]
    car += [(90.878, 114.928, -227.195), (90.878, 29.606, -227.195), ]
    car += [(-90.878, 29.606, -227.195), (-90.878, 29.606, -113.598), ]
    car += [(-90.878, 29.606, 113.598), (-90.878, 29.606, 227.195), ]
    car += [(90.878, 29.606, 227.195), (90.878, 100.171, 227.195), ]
    car += [(-90.878, 100.171, 227.195), (-90.878, 114.928, 109.126), ]
    car += [(-90.878, 161.491, 54.004), (-90.878, 161.491, -102.348), ]
    car += [(90.878, 161.491, -102.348), (90.878, 161.491, 54.004), ]
    car += [(-90.878, 161.491, 54.004), ]
    # Arrow1
    ar1 = [(0, 0, 2), (2, 0, 1), (1, 0, 1), ]
    ar1 += [(1, 0, -2), (-1, 0, -2), (-1, 0, 1), ]
    ar1 += [(-2, 0, 1), (0, 0, 2), ]
    # Arrow2
    ar2 = [(0, 1, 4), (4, 1, 2), (2, 1, 2), ]
    ar2 += [(2, 1, -4), (-2, 1, -4), (-2, 1, 2), ]
    ar2 += [(-4, 1, 2), (0, 1, 4), (0, -1, 4), ]
    ar2 += [(4, -1, 2), (2, -1, 2), (2, -1, -4), ]
    ar2 += [(-2, -1, -4), (-2, -1, 2), (-4, -1, 2), ]
    ar2 += [(0, -1, 4), (4, -1, 2), (4, 1, 2), ]
    ar2 += [(2, 1, 2), (2, 1, -4), (2, -1, -4), ]
    ar2 += [(-2, -1, -4), (-2, 1, -4), (-2, 1, 2), ]
    ar2 += [(-4, 1, 2), (-4, -1, 2), ]
    # Arrow3
    ar3 = [(7, 0, 0), (5, 0, -5), (0, 0, -7), ]
    ar3 += [(-5, 0, -5), (-7, 0, 0), (-5, 0, 5), ]
    ar3 += [(0, 0, 7), (5, 0, 5), (7, 0, 0), ]
    ar3 += [(5, 0, 2), (7, 0, 3), (7, 0, 0), ]
    # Arrow4
    ar4 = [(0, 0, -11), (-3, 0, -8), (-2.0, 0, -8), ]
    ar4 += [(-2, 0, -6), (-5, 0, -5), (-6, 0, -2), ]
    ar4 += [(-8, 0, -2), (-8, 0, -3), (-11, 0, 0), ]
    ar4 += [(-8, 0, 3), (-8, 0, 2), (-6, 0, 2), ]
    ar4 += [(-5, 0, 5), (-2, 0, 6), (-2, 0, 8), ]
    ar4 += [(-3, 0, 8), (0, 0, 11), (3, 0, 8), ]
    ar4 += [(2, 0, 8), (2, 0, 6), (5, 0, 5), ]
    ar4 += [(6, 0, 2), (8, 0, 2), (8, 0, 3), ]
    ar4 += [(11, 0, 0), (8, 0, -3), (8, 0, -2), ]
    ar4 += [(6, 0, -2), (5, 0, -5), (2, 0, -6), ]
    ar4 += [(2, 0, -8), (3, 0, -8), (0, 0, -11), ]
    # Arrow5
    ar5 = [(-2, 0, -1), (2, 0, -1), (2, 0, -2), ]
    ar5 += [(4, 0, 0), (2, 0, 2), (2, 0, 1), ]
    ar5 += [(-2, 0, 1), (-2, 0, 2), (-4, 0, 0), ]
    ar5 += [(-2, 0, -2), (-2, 0, -1), ]
    # Pointer
    pointer = [(-1, 0, 0), (-0.7, 0, 0.7), (0, 0, 1), ]
    pointer += [(0.7, 0, 0.7), (1, 0, 0), (0.7, 0, -0.7), ]
    pointer += [(0, 0, -1), (-0.7, 0, -0.7), (-1, 0, 0), ]
    pointer += [(0, 0, 0), (0, 2, 0), ]
    # Foot
    foot = [(-4, 0, -4), (-4, 0, -7), (-3, 0, -11), ]
    foot += [(-1, 0, -12), (0, 0, -12), (1, 0, -12), ]
    foot += [(3, 0, -11), (4, 0, -7), (4, 0, -4), ]
    foot += [(-4, 0, -4), (-5, 0, 1), (-5, 0, 6), ]
    foot += [(-4, 0, 12), (-2, 0, 15), (0, 0, 15.5), ]
    foot += [(2, 0, 15), (4, 0, 12), (5, 0, 6), ]
    foot += [(5, 0, 1), (4, 0, -4), (-4, 0, -4), ]
    foot += [(4, 0, -4), ]
    # Hoof
    hoof = [(-6, 0, -5), (-6.5, 0, -1), (-6, 0, 3), ]
    hoof += [(-5.2, 0, 5.5), (-3, 0, 7.5), (0, 0, 8.2), ]
    hoof += [(3, 0, 7.5), (5.2, 0, 5.5), (6, 0, 3), ]
    hoof += [(6.5, 0, -1), (6, 0, -5), (4, 0, -5), ]
    hoof += [(4.5, 0, -1), (4, 0, 3), (3.5, 0, 4.5), ]
    hoof += [(2, 0, 6), (0, 0, 6.5), (-2, 0, 6), ]
    hoof += [(-3.5, 0, 4.5), (-4, 0, 3), (-4.5, 0, -1), ]
    hoof += [(-4, 0, -5), (-6, 0, -5), (-5.5, 0, -6.5), ]
    hoof += [(5.5, 0, -6.5), (4.5, 0, -10), (2.2, 0, -12.2), ]
    hoof += [(0, 0, -12.2), (-2.2, 0, -12.2), (-4.5, 0, -10), ]
    hoof += [(-5.5, 0, -6.5), ]
    # Hoof2
    hoof2 = [(6, 6, -12), (0, 8, -12), (-6, 6, -12), ]
    hoof2 += [(-8, 3, -13), (-8, 0, -12), (-7, 0, -10), ]
    hoof2 += [(-8, 0, -6), (-9, 0, -1), (-8, 0, 4), ]
    hoof2 += [(-5, 0, 9), (0, 0, 10), (5, 0, 9), ]
    hoof2 += [(8, 0, 4), (9, 0, -1), (8, 0, -6), ]
    hoof2 += [(7, 0, -10), (8, 0, -12), (8, 3, -13), ]
    hoof2 += [(6, 6, -12), ]
    # Square
    sqr = [(0, 1, 1), (0, 1, -1), (0, -1, -1), ]
    sqr += [(0, -1, 1), (0, 1, 1)]
    # Cross
    cross = [(0, 5, 1), (0, 5, -1), (0, 1, -1), ]
    cross += [(0, 1, -5), (0, -1, -5), (0, -1, -1), ]
    cross += [(0, -5, -1), (0, -5, 1), (0, -1, 1), ]
    cross += [(0, -1, 5), (0, 1, 5), (0, 1, 1), ]
    cross += [(0, 5, 1), ]
    # Dictionary
    ctrl = {
        "cub": cub, 
        "sph": sph, 
        "cyl": cyl, 
        "pip": pip, 
        "con": con, 
        "car": car, 
        "ar1": ar1, 
        "ar2": ar2, 
        "ar3": ar3, 
        "ar4": ar4, 
        "ar5": ar5, 
        "pointer": pointer, 
        "foot": foot, 
        "hoof": hoof, 
        "hoof2": hoof2, 
        "sqr": sqr, 
        "cross": cross, 
    }
    if not kwargs:
        tmp = input()
        coordinate = []
        try:
            for i in tmp.split(","):
                key, val = i.strip().split("=")
                if val == "True":
                    coordinate.append(ctrl[key])
                else:
                    continue
        except:
            print("The parameter is incorrect.")
    else:
        coordinate = [ctrl[i] for i in kwargs if kwargs[i]]
    result = [pm.curve(d=1, p=i) for i in coordinate]
    return result


def createJson(original_func):
    """ A decorator for creating Json files. """
    def wrapper(*args, **kwargs):
        fullPath = pm.Env().sceneName()
        if not fullPath:
            print("File not saved.")
        else:
            dir = os.path.dirname(fullPath)
            name_Ext = os.path.basename(fullPath)
            name, ext = os.path.splitext(name_Ext)
            jsonAll = [i for i in os.listdir(dir) if i.endswith('.json')]
            verDict = {}
            for i in jsonAll:
                tmp = re.search('(.*)[_v]([0-9]{4})[.].*', i)
                num = int(tmp.group(2))
                verDict[num] = tmp.group(1)
            if not verDict:
                jsonFile = dir + "/" + name + ".json"
                data = {}
            else:
                verMax = max(verDict.keys())
                jsonFile = f"{dir}/{verDict[verMax]}v%04d.json" % verMax
                with open(jsonFile) as JSON:
                    data = json.load(JSON)
            result = original_func(data, *args, **kwargs)
            with open(dir + "/" + name + ".json", 'w') as JSON:
                json.dump(data, JSON, indent=4)
            return result
    return wrapper


@createJson
def writeJSON(data: dict) -> None:
    sel = pm.ls(sl=True)
    if not sel:
        print("Nothing selected.")
    else:
        for j, k in enumerate(sel):
            if j % 2:
                continue
            else:
                obj = sel[j+1].name()
                cc = k.name()
                pm.parentConstraint(cc, obj, mo=True, w=1)
                # pm.scaleConstraint(cc, obj, mo=True, w=1)
                data[obj] = cc


@createJson
def loadJSON(data: dict) -> None:
    for obj, cc in data.items():
        pm.parentConstraint(cc, obj, mo=True, w=1)
        pm.scaleConstraint(cc, obj, mo=True, w=1)


def grouping():
    """ Grouping itself and named own """
    sel = pm.ls(sl=True)
    for i in sel:
        grp = pm.group(i, n="%s_grp" % i)
        pm.xform(grp, os=True, piv=(0,0,0))


def groupingNull():
    """ Grouping null """
    sel = pm.ls(sl=True)
    for i in sel:
        grp = pm.group(i, n=f"{i}_null", r=True, )
        pm.xform(grp, os=True, piv=(0,0,0))


def groupingEmpty():
    """ Create an empty group and match the pivot with the selector. """
    sel = pm.ls(sl=True)
    grpName = []
    for i in sel:
        grp = pm.group(em=True, n = i + "_grp")
        grpName.append(grp)
        pm.matchTransform(grp, i, pos=True, rot=True)
        try:
            mom = i.getParent()
            pm.parent(grp, mom)
        except:
            pass
        pm.parent(i, grp)
    return grpName


def deletePlugins():
    """ Attempt to delete unused plugins. """
    unknownList = pm.ls(type="unknown")
    # Just delete Unknown type list.
    pm.delete(unknownList)
    pluginList = pm.unknownPlugin(q=True, l=True)
    if not pluginList:
        print("There are no unknown plugins.")
    else:
        for j, k in enumerate(pluginList):
            pm.unknownPlugin(k, r=True)
            # Print deleted plugin's names and number
            print(f"{j} : {k}")
        print('Delete completed.')


def selectObj():
    """ Select mesh only. """
    sel = pm.ls(sl=True, dag=True, type=['mesh', 'nurbsSurface'])
    obj = {i.getParent() for i in sel}
    result = list(obj)
    pm.select(result)


def selectGrp():
    """ If there is no shape and the object type is not 
    'joint', 'ikEffector', 'ikHandle', and 'Constraint', 
    then it is most likely a group. """
    sel = pm.ls(sl=True, dag=True, type=['transform'])
    grp = []
    for i in sel:
        typ = pm.objectType(i)
        A = pm.listRelatives(i, s=True)
        B = typ in ['joint', 'ikEffector', 'ikHandle',]
        C = 'Constraint' in typ
        if not (A or B or C):
            grp.append(i)
        else:
            continue
    pm.select(grp)


def selectJnt():
    """ Select only joints. """
    sel = pm.ls(sl=True, dag=True, type=['transform'])
    grp = []
    for i in sel:
        typ = pm.objectType(i)
        if typ != 'joint':
            continue
        else:
            grp.append(i)
    pm.select(grp)


def selectVerts_influenced():
    """ Select the bone first, and the mesh at the end. """
    sel = pm.ls(sl=True)
    num = len(sel)
    if num != 2:
        return
    bone = sel[0]
    mesh = sel[-1]
    if pm.objectType(bone) != 'joint':
        print("Select the bone first.")
    elif not mesh.getShape():
        print("the mesh at the end.")
    else:
        skin = mesh.listHistory(type="skinCluster")
        pm.skinCluster(skin, e=True, siv=bone)


def check_sameName():
    """ Select objects with duplicate names. """
    sel = pm.ls(tr=True) # tr: transform object
    dup = [i for i in sel if "|" in i]
    if not dup:
        print("No duplicated names.")
    else:
        pm.select(dup)


def zeroPivot():
    """ Move pivot to zero. """
    sel = pm.ls(sl=True)
    for i in sel:
        j = f"{i}.scalePivot"
        k = f"{i}.rotatePivot"
        pm.move(0, 0, 0, j, k, rpr=True)


def rename(*arg: str) -> None:
    """ Rename by incrementing the last digit in the string. """
    if not arg:
        tmp = input()
        arg = [i.strip() for i in tmp.split(",")]
        arg = tuple(arg)
    lenArg = len(arg)
    sel = pm.ls(sl=True)
    # Given a single argument, create a new name.
    if lenArg == 1:
        txt = arg[0]
        # txtList -> ['testName', '23', '_', '17', '_grp']
        txtList = re.split(r'([^0-9]+)([0-9]*)', txt)
        txtList = [i for i in txtList if i]
        # txtDict -> {1: (23, 2), 3: (17, 2)}
        txtDict = {}
        for i, n in enumerate(txtList):
            if n.isdigit():
                txtDict[i] = (int(n), len(n))
            else:
                continue
        if len(txtDict):
            idx = max(txtDict) # idx -> 3
            numTuple = txtDict[idx] # numTuple -> (17, 2)
            num = numTuple[0] # num -> 17
            numDigit = numTuple[1] # numDigit -> 2
            for j, k in enumerate(sel):
                numStr = str(num + j) # increase by j
                numLen = len(numStr) # digit of numStr
                # Match <numStr> with the input <numDigit>
                if numLen < numDigit:
                    sub = numDigit - numLen
                    numStr = '0'*sub + numStr
                txtList[idx] = numStr
                new = ''.join(txtList) # new -> 'testName23_17_grp'
                pm.rename(k, new)
        else:
            for j, k in enumerate(sel):
                new = ''.join(txtList) + str(j)
                pm.rename(k, new)
    # Two arguments replace words.
    elif lenArg == 2:
        before = arg[0]
        after = arg[1]
        for obj in sel:
            new = obj.replace(before, after)
            pm.rename(obj, new)
    else:
        print("<New name> or <Old name, New name>")


def poleVector():
    """ Get the poleVector's position from 3 joints. """
    sel = pm.ls(sl=True) # Select three objects.
    if len(sel) != 3:
        print('Select three joints.')
    else:
        midJnt = sel[1]
        endJnt = sel[2]
        points = [pm.xform(i, q=True, ws=True, rp=True) for i in sel]
        p1, p2, p3 = [i for i in points]
        pm.select(cl=True)
        tmp1 = pm.joint(p=p1)
        tmp2 = pm.joint(p=p3)
        pm.joint(tmp1, e=True, oj='xyz', sao='yup', ch=True, zso=True)
        pm.joint(tmp2, e=True, oj='none', ch=True, zso=True)
        # o: offset, wut: worldUpType, wuo: worldUpObject
        pm.aimConstraint(endJnt, tmp1, o=(0,0,90), wut='object', wuo=midJnt)
        # cn: constraint
        pm.delete(tmp1, cn=True)
        pm.matchTransform(tmp1, midJnt, pos=True)
        loc = pm.spaceLocator()
        pm.matchTransform(loc, tmp2, pos=True, rot=True)
        # Delete temporarily used joints.
        pm.delete(tmp1)


def openFolder():
    """ Open the Windows folder 
    and copy the fullPath to the clipboard.
     """
    fullPath = pm.Env().sceneName()
    dir = os.path.dirname(fullPath)
    # copy the fullPath to the clipboard.
    # subprocess.run("clip", text=True, input=fullPath)
    os.startfile(dir)


def lineStraight():
    """ Arrange the points in a straight line.
    Use the equation of a straight line in space 
    to make a curved line a straight line.
    1. Create an equation
    2. Check the condition.
    3. Make a straight line.
     """
    sel = pm.ls(sl=True, fl=True)
    if not sel:
        print('Nothing selected.')
        return
    alpha = sel[0]
    omega = sel[-1]
    # Copy the original backUp
    tmp = pm.ls(sel, o=True)
    dup = pm.duplicate(tmp, rr=True)
    dup = dup[0]
    # makeEquation
    X1, Y1, Z1 = alpha.getPosition(space="world")
    X2, Y2, Z2 = omega.getPosition(space="world")
    A, B, C = (X2 - X1), (Y2 - Y1), (Z2 - Z1)
    MAX = max([abs(i) for i in [A, B, C]])
    x, y, z = sympy.symbols('x y z')
    expr1 = sympy.Eq(B*x - A*y, B*X1 - A*Y1)
    expr2 = sympy.Eq(C*y - B*z, C*Y1 - B*Z1)
    expr3 = sympy.Eq(A*z - C*x, A*Z1 - C*X1)
    # Conditions
    if abs(A) == MAX:
        idx = 0
        xyz = x
        variables = [y, z]
        expr = [expr1, expr3]
    elif abs(B) == MAX:
        idx = 1
        xyz = y
        variables = [x, z]
        expr = [expr1, expr2]
    elif abs(C) == MAX:
        idx = 2
        xyz = z
        variables = [x, y]
        expr = [expr2, expr3]
    else:
        pass
    # makeStraight
    for i in sel:
        point = i.getPosition(space="world")
        value = point[idx]
        fx = [i.subs(xyz, value) for i in expr]
        sol = sympy.solve(fx, variables)
        sol[xyz] = value
        p1, p2, p3 = [round(float(sol[var]), 4) for var in [x, y, z]]
        pm.move(p1, p2, p3, i)


def lineStraight_rebuild():
    """ This way does not create an equation, 
    but uses rebuild to create a straight line. """
    sel = pm.ls(sl=True, fl=True)
    spans = len(sel) - 1
    alpha = sel[0].getPosition(space="world")
    omega = sel[-1].getPosition(space="world")
    cuv = pm.curve(d=1, p=[alpha, omega])
    pm.rebuildCurve(cuv, d=1, 
        ch=False, # constructionHistory
        s=spans, # spans
        rpo=True, # replaceOriginal
        end=1, # endKnots
        kr=0, # keepRange
        kt=0, # keepTangents
        )


def orientJnt() -> list:
    """ Freeze and Orient joints
    Select only "joint", freeze and orient. 
    And the end joints inherit the orient of the parent joint.
     """
    sel = pm.ls(sl=True)
    pm.select(sel, hi=True)
    allJnt = [i for i in pm.ls(sl=True) if pm.objectType(i)=='joint']
    endJnt = [i for i in allJnt if not i.getChildren()]
    pm.select(cl=True)
    # freeze joints
    pm.makeIdentity(allJnt, a=True, jo=True, n=0)
    # orient joints
    pm.joint(sel[0], e=True, oj='xyz', sao='yup', ch=True, zso=True)
    # orient end joints
    for i in endJnt:
        pm.joint(i, e=True, oj='none', ch=True, zso=True)


def jntNone(*arg: int) -> None:
    '''Change the drawing style of a joint.
    0: Bone
    1: Multi Child as Box
    2: None
    '''
    num = 2 if not arg else arg[0]
    sel = pm.ls(sl=True)
    if num < 0 or num > 2:
        msg = "Allowed numbers are "
        msg += "[0: Bone, 1: Multi Child as Box, 2: None]"
        print(msg)
    elif not sel:
        print("Nothing selected.")
    else:
        jnt = [i for i in sel if pm.objectType(i)=='joint']
        for i in jnt:
            pm.setAttr(f"{i}.drawStyle", num)


def copyHJK():
    """ Copy hjk.py 
    from <in git folder> to <maya folder in MyDocuments> """
    gitFolder = r"C:\Users\jkhong\Desktop\git\maya\hjk.py"
    docFolder = r"C:\Users\jkhong\Documents\maya\scripts\hjk.py"
    shutil.copy(gitFolder, docFolder)


# 79 char line ================================================================
# 72 docstring or comments line ========================================


sel = pm.ls(sl=True)
num = len(sel)

countSetRange = (num//3) + (1 if num%3 else 0)
setRangeList = []
for i in range(countSetRange):
    tmp = pm.shadingNode("setRange", au=True)
    pm.setAttr(f"{tmp}.maxX", 180)
    pm.setAttr(f"{tmp}.maxY", 180)
    pm.setAttr(f"{tmp}.maxZ", 180)
    pm.setAttr(f"{tmp}.oldMinX", 0 + (i * 3))
    pm.setAttr(f"{tmp}.oldMinY", 1 + (i * 3))
    pm.setAttr(f"{tmp}.oldMinZ", 2 + (i * 3))
    pm.setAttr(f"{tmp}.oldMaxX", 1 + (i * 3))
    pm.setAttr(f"{tmp}.oldMaxY", 2 + (i * 3))
    pm.setAttr(f"{tmp}.oldMaxZ", 3 + (i * 3))
    setRangeList.append(tmp)


for j, k in enumerate(sel):
    prev = sel[j-1]
    curr = k
    next = sel[0] if j+1 >= num else sel[j+1]
    setRangeNode = setRangeList[j//3]
    print(setRangeNode, j//3)
    plusMinusNode = pm.shadingNode("plusMinusAverage", au=True)
    pm.setAttr(f"{plusMinusNode}.operation", 2)
    pm.setAttr(f"{plusMinusNode}.input1D[1]", 180)
    out = ["outValueX", "outValueY", "outValueZ"]
    pm.connectAttr(f"{setRangeNode}.{out[j%3]}", f"{k}.rotateX", f=True)
    pm.connectAttr(f"{k}.rotateX", f"{plusMinusNode}.input1D[0]", f=True)
    pm.connectAttr(f"{plusMinusNode}.output1D", f"{prev}.visibility", f=True)
    



