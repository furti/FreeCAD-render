from __future__ import print_function
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

# Appleseed renderer for FreeCAD

# This file can also be used as a template to add more rendering engines.
# You will need to make sure your file is named with a same name (case sensitive)
# That you will use everywhere to describe your renderer, ex: Appleseed or Povray


# A render engine module must contain the following functions:
#
#    writeCamera(por,rot,up,target): returns a string containing an openInventor camera string in renderer format
#    writeObject(view,mesh,material): returns a string containing a RaytracingView object in renderer format
#    render(project,prefix,external,output,width,height): renders the given project, external means
#                                                         if the user wishes to open the render file
#                                                         in an external application/editor or not. If this
#                                                         is not supported by your renderer, you can simply
#                                                         ignore it
#
# Additionally, you might need/want to add:
#
#    Preference page items, that can be used in your functions below
#    An icon under the name Renderer.svg (where Renderer is the name of your Renderer


import tempfile
import FreeCAD
import os
import math
import re


def writeCamera(pos,rot,up,target):

    # this is where you create a piece of text in the format of
    # your renderer, that represents the camera.

    target = str(target.x)+" "+str(target.y)+" "+str(target.z)
    up = str(up.x)+" "+str(up.y)+" "+str(up.z)
    pos = str(pos.x)+" "+str(pos.y)+" "+str(pos.z)

    cam = """
        <camera name="camera" model="thinlens_camera">
            <parameter name="film_width" value="0.032" />
            <parameter name="aspect_ratio" value="1.7" />
            <parameter name="horizontal_fov" value="80" />
            <parameter name="shutter_open_time" value="0" />
            <parameter name="shutter_close_time" value="1" />
            <transform>
                <look_at origin="%s" target="%s" up="%s" />
            </transform>
        </camera>""" % (pos, target, up)

    return cam


def writeObject(viewobj,mesh,color,material):

    # This is where you write your object/view in the format of your
    # renderer. "obj" is the real 3D object handled by this project, not
    # the project itself. This is your only opportunity
    # to write all the data needed by your object (geometry, materials, etc)
    # so make sure you include everything that is needed
    #
    # material is a object with the folowing properties
    #  - color: the color for the object
    #  - alpha: the alpha value for the object

    objname = viewobj.Name
    colorname = objname + "_color"
    bsdfname = objname + "_bsdf"
    matname = objname + "_mat"

    # format color and alpha

    color = str(material.color[0])+" "+str(material.color[1])+" "+str(material.color[2])
    alpha = str(material.alpha)

    # write the mesh as an obj tempfile

    meshfile = tempfile.mkstemp(suffix=".obj", prefix="_")[1]
    objfile = os.path.splitext(os.path.basename(meshfile))[0]
    mesh.write(meshfile)

    # fix for missing object name in obj file (mandatory in Appleseed)

    f = open(meshfile, "r")
    contents = f.readlines()
    f.close()
    n = []
    found = False
    for l in contents:
        if (not found) and l.startswith("f "):
            found = True
            n.append("o "+objname+"\n")
        n.append(l)
    f = open(meshfile, "w")
    contents = "".join(n)
    f.write(contents)
    f.close()

    objdef = """
            <color name="%s">
                <parameter name="color_space" value="linear_rgb" />
                <parameter name="multiplier" value="1.0" />
                <parameter name="wavelength_range" value="400.0 700.0" />
                <values>
                    %s
                </values>
                <alpha>
                    %s
                </alpha>
            </color>
            <bsdf name="%s" model="lambertian_brdf">
                <parameter name="reflectance" value="%s" />
            </bsdf>
            <material name="%s" model="generic_material">
                <parameter name="bsdf" value="%s" />
                <parameter name="bump_amplitude" value="1.0" />
                <parameter name="bump_offset" value="2.0" />
                <parameter name="displacement_method" value="bump" />
                <parameter name="normal_map_up" value="z" />
                <parameter name="shade_alpha_cutouts" value="false" />
            </material>
            <object name="%s" model="mesh_object">
                <parameter name="filename" value="%s" />
            </object>
            <object_instance name="%s.instance" object="%s">
                <assign_material slot="default" side="front" material="%s" />
                <assign_material slot="default" side="back" material="%s" />
            </object_instance>""" % (colorname, color, alpha,
                                    bsdfname, colorname,
                                    matname, bsdfname,
                                    objfile, meshfile,
                                    objfile+"."+objname,
                                    objfile+"."+objname,
                                    matname, matname)

    return objdef


def render(project,prefix,external,output,width,height):

    # here you trigger a render by firing the renderer
    # executable and passing it the needed arguments, and
    # the file it needs to render

    # change image size in template
    f = open(project.PageResult,"r")
    t = f.read()
    f.close()
    res = re.findall("<parameter name=\"resolution.*?\/>",t)
    if res:
        t = t.replace(res[0],"<parameter name=\"resolution\" value=\""+str(width)+" "+str(height)+"\" />")
        fp = tempfile.mkstemp(prefix=project.Name,suffix=os.path.splitext(project.Template)[-1])[1]
        f = open(fp,"w")
        f.write(t)
        f.close()
        project.PageResult = fp
        os.remove(fp)
        FreeCAD.ActiveDocument.recompute()

    p = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Render")
    if external:
        rpath = p.GetString("AppleseedStudioPath","")
        args = ""
    else:
        rpath = p.GetString("AppleseedCliPath","")
        args = p.GetString("AppleseedParameters","")
        if args:
            args += " "
        args += "--output "+output
    if not rpath:
        FreeCAD.Console.PrintError("Unable to locate renderer executable. Please set the correct path in Edit -> Preferences -> Render")
        return
    if args:
        args += " "
    os.system('"' + prefix+rpath+'" '+args+project.PageResult)
    return


