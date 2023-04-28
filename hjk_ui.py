import pymel.core as pm
import hjk


winName = 'hjkButton'
if pm.window(winName, exists=True):
    pm.deleteUI(winName)
else:
    win = pm.window(winName, t='hjkButton', s=True, rtf=True)
    pm.columnLayout(cat=('both', 4), rowSpacing=2, columnWidth=188)
    pm.separator(h=10)
    pm.rowColumnLayout(nc=2, cw=[(1, 90), (2, 90)])
    pm.button(l='Han', c=lambda x: hjk.Han())
    pm.button(l='SoftSel', c=lambda x: hjk.SoftSel())
    pm.button(l='AutoWheel_Rig', c=lambda x: hjk.AutoWheel_Rig())
    pm.button(l='AutoWheel_Key', c=lambda x: hjk.AutoWheel_Key())
    pm.button(l='MatchPivot', c=lambda x: hjk.MatchPivot())
    pm.button(l='MatchCuvShp', c=lambda x: hjk.MatchCuvShp())
    pm.button(l='MirrorCopy_X', c=lambda x: hjk.MirrorCopy(x=True))
    pm.button(l='MirrorCopy_Z', c=lambda x: hjk.MirrorCopy(z=True))
    pm.button(l='VertexSelector', c=lambda x: hjk.VertexSeletor())
    pm.button(l='LineConnect', c=lambda x: hjk.LineConnect())
    pm.button(l='Colors', c=lambda x: hjk.Colors())
    pm.button(l='SolariBoard', c=lambda x: hjk.SolariBoard())
    pm.button(l='cuv_thruLoc', c=lambda x: hjk.createCuv_thruLoc())
    pm.button(l='cuv_thruLoc_Closed', c=lambda x: hjk.createCuv_thruLoc(cl=True))
    pm.button(l='creatLoc', c=lambda x: hjk.createLoc())
    pm.button(l='createLine', c=lambda x: hjk.createLine())
    pm.button(l='jnt_MotionPath', c=lambda x: hjk.createJnt_MotionPath())
    pm.button(l='ctrl', c=lambda x: hjk.ctrl())
    pm.button(l='writeJSON', c=lambda x: hjk.writeJSON())
    pm.button(l='loadJSON', c=lambda x: hjk.loadJSON())
    pm.button(l='grouping', c=lambda x: hjk.grouping())
    pm.button(l='groupingNull', c=lambda x: hjk.groupingNull())
    pm.button(l='groupingEmpty', c=lambda x: hjk.groupingEmpty())
    pm.button(l='deletePlugins', c=lambda x: hjk.deletePlugins())
    pm.button(l='selectObj', c=lambda x: hjk.selectObj())
    pm.button(l='selectGrp', c=lambda x: hjk.selectGrp())
    pm.button(l='selectConst', c=lambda x: hjk.selectConst())
    pm.button(l='selectJnt', c=lambda x: hjk.selectJnt())
    pm.button(l='selectVerts_influenced', c=lambda x: hjk.selectVerts_influenced())
    pm.button(l='check_sameName', c=lambda x: hjk.check_sameName())
    pm.button(l='zeroPivot', c=lambda x: hjk.zeroPivot())
    pm.button(l='poleVector', c=lambda x: hjk.poleVector())
    pm.button(l='openFolder', c=lambda x: hjk.openFolder())
    pm.button(l='lineStraight', c=lambda x: hjk.lineStraight())
    pm.button(l='lineStraight_rebuild', c=lambda x: hjk.lineStraight_rebuild())
    pm.button(l='orientJnt', c=lambda x: hjk.orientJnt())
    pm.button(l='jntNone', c=lambda x: hjk.jntNone(2))
    pm.button(l='jntBone', c=lambda x: hjk.jntNone(0))
    pm.button(l='attr_geoHide', c=lambda x: hjk.attr_geoHide())
    pm.button(l='attr_subCtrl', c=lambda x: hjk.attr_subCtrl())
    pm.button(l='getPointPosition', c=lambda x: hjk.getPointPosition())
    pm.button(l='copyHJK', c=lambda x: hjk.copyHJK())
    pm.setParent("..", u=True)
    pm.separator(h=10)
    pm.showWindow(win)
