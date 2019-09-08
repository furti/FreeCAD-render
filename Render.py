#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2017 Yorik van Havre <yorik@uncreated.net>              *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

# This module handles all the external renderers implemented as Python modules.
# It will add all renderer modules specified below at FreeCAD launch, and
# create the necessary UI controls.

import sys
import os
import re
import tempfile
import FreeCAD
import importlib
import math

if FreeCAD.GuiUp:
    from PySide import QtCore, QtGui
    def translate(context, text):
        if sys.version_info.major >= 3:
            if hasattr(QtGui.QApplication,"UnicodeUTF8"):
                return QtGui.QApplication.translate(context, text, None, QtGui.QApplication.UnicodeUTF8)
            else:
                return QtGui.QApplication.translate(context, text, None)
        else:
            if hasattr(QtGui.QApplication,"UnicodeUTF8"):
                return QtGui.QApplication.translate(context, text, None, QtGui.QApplication.UnicodeUTF8).encode("utf8")
            else:
                return QtGui.QApplication.translate(context, text, None).encode("utf8")
else:
    def translate(context,txt):
        return txt
def QT_TRANSLATE_NOOP(scope, text):
    return text

def doRender(project, external=True):
    img = project.Proxy.render(project,external)
    
    if img and hasattr(project,"OpenAfterRender") and project.OpenAfterRender:
        import ImageGui
        ImageGui.open(img)


class RenderProjectCommand:


    "Creates a rendering project. The renderer parameter must be a valid rendering module"

    def __init__(self,renderer):
        self.renderer = renderer

    def GetResources(self):
        return {'Pixmap'  : os.path.join(os.path.dirname(__file__),"icons",self.renderer+".svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Render", "%s Project") % self.renderer,
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Render", "Creates a %s project") % self.renderer}

    def Activated(self):
        if self.renderer:
            project = FreeCAD.ActiveDocument.addObject("App::FeaturePython",self.renderer+"Project")
            Project(project)
            project.Label = self.renderer + " Project"
            project.Renderer = self.renderer
            ViewProviderProject(project.ViewObject)
            filename = QtGui.QFileDialog.getOpenFileName(FreeCADGui.getMainWindow(),'Select template',os.path.join(os.path.dirname(__file__),"templates"),'*.*')
            if filename:
                project.Template = filename[0]
            project.ViewObject.Proxy.setCamera()
            FreeCAD.ActiveDocument.recompute()



class RenderViewCommand:


    "Creates a Raytracing view of the selected object(s) in the selected project or the default project"

    def GetResources(self):
        return {'Pixmap'  : os.path.join(os.path.dirname(__file__),"icons","RenderView.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Render", "Create View"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Render", "Creates a Render view of the selected object(s) in the selected project or the default project")}

    def Activated(self):
        import FreeCADGui
        project = None
        objs = []
        sel = FreeCADGui.Selection.getSelection()
        for o in sel:
            if "Renderer" in o.PropertiesList:
                project = o
            else:
                if o.isDerivedFrom("Part::Feature") or o.isDerivedFrom("Mesh::Feature"):
                    objs.append(o)
        if not project:
            for o in FreeCAD.ActiveDocument.Objects:
                if "Renderer" in o.PropertiesList:
                    project = o
                    break
        if not project:
            FreeCAD.Console.PrintError(translate("Render","Unable to find a valid project in selection or document"))
            return
        for obj in objs:
            view = FreeCAD.ActiveDocument.addObject("App::FeaturePython",obj.Name+"View")
            view.Label = "View of "+ obj.Name
            View(view)
            view.Source = obj
            project.addObject(view)
            ViewProviderView(view.ViewObject)
        FreeCAD.ActiveDocument.recompute()



class RenderCommand:


    "Renders a selected Render project"


    def GetResources(self):
        return {'Pixmap'  : os.path.join(os.path.dirname(__file__),"icons","Render.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Render", "Render"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Render", "Performs the render of a selected project or the default project")}

    def Activated(self):
        import FreeCADGui
        project = None
        sel = FreeCADGui.Selection.getSelection()
        for o in sel:
            if "Renderer" in o.PropertiesList:
                project = o
                break
        if not project:
            for o in FreeCAD.ActiveDocument.Objects:
                if "Renderer" in o.PropertiesList:
                    project = o
                    break
        if not project:
            FreeCAD.Console.PrintError(translate("Render","Unable to find a valid project in selection or document"))
            return
        doRender(project)

class RenderExternalCommand:


    "Sends a selected Render project"


    def GetResources(self):

        return {'Pixmap'  : os.path.join(os.path.dirname(__file__),"icons","Render.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Render", "Render"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Render", "Performs the render of a selected project or the default project")}

    def Activated(self):

        import FreeCADGui
        project = None
        sel = FreeCADGui.Selection.getSelection()
        for o in sel:
            if "Renderer" in o.PropertiesList:
                project = o
                break
        if not project:
            for o in FreeCAD.ActiveDocument.Objects:
                if "Renderer" in o.PropertiesList:
                    project = o
                    break
        if not project:
            FreeCAD.Console.PrintError(translate("Render","Unable to find a valid project in selection or document"))
            return
        doRender(project, external=True)

class Project:


    "A rendering project"


    def __init__(self,obj):

        obj.Proxy = self
        self.setProperties(obj)


    def setProperties(self,obj):

        if not "Renderer" in obj.PropertiesList:
            obj.addProperty("App::PropertyString","Renderer","Render", QT_TRANSLATE_NOOP("App::Property","The name of the raytracing engine to use"))
        if not "DelayedBuild" in obj.PropertiesList:
            obj.addProperty("App::PropertyBool","DelayedBuild","Render", QT_TRANSLATE_NOOP("App::Property","If true, the views will be updated on render only"))
            obj.DelayedBuild = True
        if not "Template" in obj.PropertiesList:
            obj.addProperty("App::PropertyFile","Template","Render", QT_TRANSLATE_NOOP("App::Property","The template to be use by this rendering"))
        if not "Camera" in obj.PropertiesList:
            obj.addProperty("App::PropertyString","Camera","Render", QT_TRANSLATE_NOOP("App::Property","The camera data to be used"))
        if not "PageResult" in obj.PropertiesList:
            obj.addProperty("App::PropertyFileIncluded", "PageResult","Render", QT_TRANSLATE_NOOP("App::Property","The result file to be sent to the renderer"))
        if not "Group" in obj.PropertiesList:
            obj.addExtension("App::GroupExtensionPython", self)
        if not "RenderWidth" in obj.PropertiesList:
            obj.addProperty("App::PropertyInteger","RenderWidth","Render", QT_TRANSLATE_NOOP("App::Property","The width of the rendered image in pixels"))
            obj.RenderWidth = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Render").GetInt("RenderWidth",800)
        if not "RenderHeight" in obj.PropertiesList:
            obj.addProperty("App::PropertyInteger","RenderHeight","Render", QT_TRANSLATE_NOOP("App::Property","The height of the rendered image in pixels"))
            obj.RenderHeight = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Render").GetInt("RenderHeight",600)
        if not "GroundPlane" in obj.PropertiesList:
            obj.addProperty("App::PropertyBool","GroundPlane","Render", QT_TRANSLATE_NOOP("App::Property","If true, a default ground plane will be added to the scene"))
            obj.GroundPlane = False
        if not "OutputImage" in obj.PropertiesList:
            obj.addProperty("App::PropertyFile","OutputImage","Render", QT_TRANSLATE_NOOP("App::Property","The image saved by this render"))
        if not "OpenAfterRender" in obj.PropertiesList:
            obj.addProperty("App::PropertyBool","OpenAfterRender","Render", QT_TRANSLATE_NOOP("App::Property","If true, the rendered image is opened in FreeCAD after the rendering is finished"))
            obj.GroundPlane = False
        obj.setEditorMode("PageResult",2)
        obj.setEditorMode("Camera",2)


    def onDocumentRestored(self,obj):

        self.setProperties(obj)


    def execute(self,obj):

        return True


    def onChanged(self,obj,prop):

        if prop == "DelayedBuild":
            if not obj.DelayedBuild:
                for view in obj.Group:
                    view.touch()


    def setCamera(self,obj):

        if FreeCAD.GuiUp:
            import FreeCADGui
            obj.Camera = FreeCADGui.ActiveDocument.ActiveView.getCamera()


    def writeCamera(self,obj):

        # camdata contains a string in OpenInventor format
        # ex:
        # #Inventor V2.1 ascii
        #
        #
        # PerspectiveCamera {
        #  viewportMapping ADJUST_CAMERA
        #  position 0 -1.3207401 0.82241058
        #  orientation 0.99999666 0 0  0.26732138
        #  nearDistance 1.6108983
        #  farDistance 6611.4492
        #  aspectRatio 1
        #  focalDistance 5
        #  heightAngle 0.78539819
        #
        # }
        #
        # or (ortho camera):
        #
        # #Inventor V2.1 ascii
        #
        #
        # OrthographicCamera {
        #  viewportMapping ADJUST_CAMERA
        #  position 0 0 1
        #  orientation 0 0 1  0
        #  nearDistance 0.99900001
        #  farDistance 1.001
        #  aspectRatio 1
        #  focalDistance 5
        #  height 4.1421356
        #
        # }

        if not obj.Camera:
            self.setCamera(obj)
            if not obj.Camera:
                FreeCAD.Console.PrintError(translate("Render","Unable to set the camera"))
                return ""
        if obj.Renderer:
            try:
                renderer = importlib.import_module("renderers."+obj.Renderer)
            except ImportError:
                FreeCAD.Console.PrintError(translate("Render","Error importing renderer")+" "+str(obj.Renderer))
                return ""
            else:

                if not obj.Camera:
                    return ""
                camdata = obj.Camera.split("\n")
                cam = ""
                pos = [float(p) for p in camdata[5].split()[-3:]]
                pos = FreeCAD.Vector(pos)
                rot = [float(p) for p in camdata[6].split()[-4:]]
                rot = FreeCAD.Rotation(FreeCAD.Vector(rot[0],rot[1],rot[2]),math.degrees(rot[3]))
                target = rot.multVec(FreeCAD.Vector(0,0,-1))
                target.multiply(float(camdata[10].split()[-1]))
                target = pos.add(target)
                up = rot.multVec(FreeCAD.Vector(0,1,0))

                return renderer.writeCamera(pos,rot,up,target)


    def writeObject(self,obj,view):

        if not view.Source:
            return ""
        if obj.Renderer:
            try:
                renderer = importlib.import_module("renderers."+obj.Renderer)
            except ImportError:
                FreeCAD.Console.PrintError(translate("Render","Error importing renderer")+" "+str(obj.Renderer))
                return ""
            else:

                # get color and alpha
                mat = None
                color = None
                alpha = None
                if view.Material:
                    mat = view.Material
                else:
                    if "Material" in view.Source.PropertiesList:
                        if view.Source.Material:
                            mat = view.Source.Material
                if mat:
                    if "Material" in mat.PropertiesList:
                        if "DiffuseColor" in mat.Material:
                            color = mat.Material["DiffuseColor"].strip("(").strip(")").split(",")[:3]
                        if "Transparency" in mat.Material:
                            if float(mat.Material["Transparency"]) > 0:
                                alpha = 1.0-float(mat.Material["Transparency"])
                            else:
                                alpha = 1.0
                if view.Source.ViewObject:
                    if not color:
                        if hasattr(view.Source.ViewObject,"ShapeColor"):
                            color = view.Source.ViewObject.ShapeColor[:3]
                    if not alpha:
                        if hasattr(view.Source.ViewObject,"Transparency"):
                            if view.Source.ViewObject.Transparency > 0:
                                alpha = 1.0-(float(view.Source.ViewObject.Transparency)/100.0)
                if not color:
                    color = (1.0, 1.0, 1.0)
                if not alpha:
                    alpha = 1.0

                # get mesh
                import Draft
                import Part
                import MeshPart
                mesh = None
                if hasattr(view.Source,"Group"):
                    shps = [o.Shape for o in Draft.getGroupContents(view.Source) if hasattr(o,"Shape")]
                    mesh = MeshPart.meshFromShape(Shape=Part.makeCompound(shps),
                                               LinearDeflection=0.1,
                                               AngularDeflection=0.523599,
                                               Relative=False)
                elif view.Source.isDerivedFrom("Part::Feature"):
                    mesh = MeshPart.meshFromShape(Shape=view.Source.Shape,
                                               LinearDeflection=0.1,
                                               AngularDeflection=0.523599,
                                               Relative=False)
                elif view.Source.isDerivedFrom("Mesh::Feature"):
                    mesh = view.Source.Mesh
                if not mesh:
                    return ""

                return renderer.writeObject(view,mesh,color,alpha)


    def writeGroundPlane(self,obj):

        result = ""
        bbox = FreeCAD.BoundBox()
        for view in obj.Group:
            if view.Source and hasattr(view.Source,"Shape") and hasattr(view.Source.Shape,"BoundBox"):
                bbox.add(view.Source.Shape.BoundBox)
        if bbox.isValid():
            import Part
            margin = bbox.DiagonalLength/2
            p1 = FreeCAD.Vector(bbox.XMin-margin,bbox.YMin-margin,0)
            p2 = FreeCAD.Vector(bbox.XMax+margin,bbox.YMin-margin,0)
            p3 = FreeCAD.Vector(bbox.XMax+margin,bbox.YMax+margin,0)
            p4 = FreeCAD.Vector(bbox.XMin-margin,bbox.YMax+margin,0)

            # create temporary object. We do this to keep the renderers code as simple as possible:
            # they only need to deal with one type of object: RenderView objects
            dummy1 = FreeCAD.ActiveDocument.addObject("Part::Feature","renderdummy1")
            dummy1.Shape = Part.Face(Part.makePolygon([p1,p2,p3,p4,p1]))
            dummy2 = FreeCAD.ActiveDocument.addObject("App::FeaturePython","renderdummy2")
            View(dummy2)
            dummy2.Source = dummy1
            ViewProviderView(dummy2.ViewObject)
            FreeCAD.ActiveDocument.recompute()

            result = self.writeObject(obj,dummy2)

            # remove temp objects
            FreeCAD.ActiveDocument.removeObject(dummy2.Name)
            FreeCAD.ActiveDocument.removeObject(dummy1.Name)
            FreeCAD.ActiveDocument.recompute()

        return result


    def render(self,obj,external=True):

        if obj.Renderer:

            # open template
            template = None
            if obj.Template:
                if os.path.exists(obj.Template):
                    f = open(obj.Template,"r")
                    template = f.read()
                    if sys.version_info.major < 3:
                        template = template.decode("utf8")
                    f.close()
            if not template:
                return

            # write camera
            cam = self.writeCamera(obj)

            # write objects
            renderobjs = ""
            for view in obj.Group:
                if obj.DelayedBuild:
                    renderobjs += self.writeObject(obj,view)
                else:
                    renderobjs += view.ViewResult
            if hasattr(obj,"GroundPlane") and obj.GroundPlane:
                renderobjs += self.writeGroundPlane(obj)

            if "RaytracingCamera" in template:
                template = re.sub("(.*RaytracingCamera.*)",cam,template)
                template = re.sub("(.*RaytracingContent.*)",renderobjs,template)
            else:
                template = re.sub("(.*RaytracingContent.*)",cam+"\n"+renderobjs,template)

            # save page result
            fp = tempfile.mkstemp(prefix=obj.Name,suffix=os.path.splitext(obj.Template)[-1])[1]
            f = open(fp,"w")
            if sys.version_info.major < 3:
                template = template.encode("utf8")
            f.write(template)
            f.close()
            obj.PageResult = fp
            os.remove(fp)

            FreeCAD.ActiveDocument.recompute()

            # run the rendering
            try:
                renderer = importlib.import_module("renderers."+obj.Renderer)
            except ImportError:
                FreeCAD.Console.PrintError(translate("Render","Error importing renderer")+" "+str(obj.Renderer))
                return
            else:
                if not obj.PageResult:
                    FreeCAD.Console.PrintError(translate("Render","Error: No page result"))
                    return
                p = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Render")
                prefix = p.GetString("Prefix","")
                if prefix:
                    prefix += " "
                output = os.path.splitext(obj.PageResult)[0]+".png"
                if hasattr(obj,"OutputImage") and obj.OutputImage:
                    output = obj.OutputImage
                width = 800
                if hasattr(obj,"RenderWidth") and obj.RenderWidth:
                    width = obj.RenderWidth
                height = 600
                if hasattr(obj,"RenderHeight") and obj.RenderHeight:
                    height = obj.RenderHeight
                return renderer.render(obj,prefix,external,output,width,height)
                FreeCAD.Console.PrintError(translate("Render","Error while executing renderer")+" "+str(obj.Renderer) + ": " + traceback.format_exc()+"\n")


class ViewProviderProject:


    def __init__(self,vobj):
        vobj.Proxy = self

    def attach(self,vobj):
        self.Object = vobj.Object
        return True

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

    def getDisplayModes(self,vobj):
        return ["Default"]

    def getDefaultDisplayMode(self):
        return "Default"

    def setDisplayMode(self,mode):
        return mode

    def isShow(self):
        return True

    def getIcon(self):
        return os.path.join(os.path.dirname(__file__),"icons","RenderProject.svg")

    def setupContextMenu(self,vobj,menu):
        from PySide import QtCore,QtGui
        import FreeCADGui
        action1 = QtGui.QAction(QtGui.QIcon(":/icons/camera-photo.svg"),"Save camera position",menu)
        QtCore.QObject.connect(action1,QtCore.SIGNAL("triggered()"),self.setCamera)
        menu.addAction(action1)
        action2 = QtGui.QAction(QtGui.QIcon(os.path.join(os.path.dirname(__file__),"icons","Render.svg")),"Render",menu)
        QtCore.QObject.connect(action2,QtCore.SIGNAL("triggered()"),self.render)
        menu.addAction(action2)

    def setCamera(self):
        if hasattr(self,"Object"):
            self.Object.Proxy.setCamera(self.Object)

    def render(self):
        if hasattr(self,"Object"):
            doRender(self.Object)

    def claimChildren(self):
        if hasattr(self,"Object"):
            return self.Object.Group


class View:


    "A rendering view"

    def __init__(self,obj):

        obj.addProperty("App::PropertyLink",         "Source",     "Render", QT_TRANSLATE_NOOP("App::Property","The name of the raytracing engine to use"))
        obj.addProperty("App::PropertyLink",         "Material",   "Render", QT_TRANSLATE_NOOP("App::Property","The template to be use by this rendering"))
        obj.addProperty("App::PropertyString",       "ViewResult", "Render", QT_TRANSLATE_NOOP("App::Property","The rendering output of this view"))
        obj.Proxy = self

    def execute(self,obj):

        for proj in obj.InList:
            if hasattr(proj,"Group"):
                for c in proj.Group:
                    if c == obj:
                        if not proj.DelayedBuild:
                            obj.ViewResult = proj.Proxy.writeObject(proj,obj)
                            break


class ViewProviderView:


    def __init__(self,vobj):
        vobj.Proxy = self

    def attach(self,vobj):
        self.Object = vobj.Object

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

    def getDisplayModes(self,vobj):
        return ["Default"]

    def getDefaultDisplayMode(self):
        return "Default"

    def setDisplayMode(self,mode):
        return mode

    def isShow(self):
        return True

    def getIcon(self):
        return os.path.join(os.path.dirname(__file__),"icons","RenderViewTree.svg")



# Load available renderers and create the FreeCAD commands



if FreeCAD.GuiUp:

    import FreeCADGui

    RenderCommands = []
    Renderers = os.listdir(os.path.dirname(__file__)+os.sep+"renderers")
    Renderers = [r for r in Renderers if not ".pyc" in r]
    Renderers = [r for r in Renderers if not "__" in r]
    Renderers = [os.path.splitext(r)[0] for r in Renderers]
    for renderer in Renderers:
        FreeCADGui.addCommand('Render_'+renderer, RenderProjectCommand(renderer))
        RenderCommands.append('Render_'+renderer)
    FreeCADGui.addCommand('Render_View', RenderViewCommand())
    RenderCommands.append('Render_View')
    FreeCADGui.addCommand('Render_Render', RenderCommand())
    RenderCommands.append('Render_Render')

    # This is for InitGui.py because it cannot import os
    iconpath = os.path.join(os.path.dirname(__file__),"icons")
    prefpage = os.path.join(os.path.dirname(__file__),"ui","RenderSettings.ui")
