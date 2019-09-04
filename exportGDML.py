#***************************************************************************
#*                                                                         
#*   Copyright (c) 2019 Keith Sloan <keith@sloan-home.co.uk>              *
#*                                                                        *
#*   This program is free software; you can redistribute it and/or modify *
#*   it under the terms of the GNU Lesser General Public License (LGPL)   *
#*   as published by the Free Software Foundation; either version 2 of    *
#*   the License, or (at your option) any later version.                  *
#*   for detail see the LICENCE text file.                                *
#*                                                                        *
#*   This program is distributed in the hope that it will be useful,      *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of       *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        *
#*   GNU Library General Public License for more details.                 *
#*                                                                        *
#*   You should have received a copy of the GNU Library General Public    *
#*   License along with this program; if not, write to the Free Software  *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 *
#*   USA                                                                  *
#*                                                                        *
#*   Acknowledgements : Ideas & code copied from                          *
#*                      https://github.com/ignamv/geanTipi                *
#*                                                                        *
#***************************************************************************
__title__="FreeCAD - GDML exporter Version"
__author__ = "Keith Sloan <keith@sloan-home.co.uk>"
__url__ = ["https://github.com/KeithSloan/FreeCAD_Geant4"]

import FreeCAD, os, Part, math
from FreeCAD import Vector

# xml handling
#import argparse
import lxml.etree  as ET
#from   xml.etree.ElementTree import XML 
#################################

try: import FreeCADGui
except ValueError: gui = False
else: gui = True

global zOrder

from GDMLObjects import GDMLQuadrangular, GDMLTriangular, \
                        GDML2dVertex, GDMLSection, \
                        GDMLmaterial, GDMLfraction, \
                        GDMLcomposite, GDMLisotope, \
                        GDMLelement, GDMLconstant

#***************************************************************************
# Tailor following to your requirements ( Should all be strings )          *
# no doubt there will be a problem when they do implement Value
if open.__module__ in ['__builtin__', 'io']:
    pythonopen = open # to distinguish python built-in open function from the one declared here

#################################
# Switch functions
################################
class switch(object):
    value = None
    def __new__(class_, value):
        class_.value = value
        return True

def case(*args):
    return any((arg == switch.value for arg in args))

#########################################################
# Pretty format GDML                                    #
#########################################################
def indent(elem, level=0):
    i = "\n" + level*"  "
    j = "\n" + (level-1)*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = j
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = j
    return elem
#################################
#  Setup GDML environment
#################################
def GDMLstructure() :
    print("Setup GDML structure")
    #################################
    # globals
    ################################
    global gdml, define, materials, solids, structure, setup, worldVOL
    global defineCnt, LVcount, PVcount, POScount, ROTcount

    defineCnt = LVcount = PVcount = POScount =  ROTcount = 1

    #gdml = ET.Element('gdml', {
          #'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance",
          #'xsi:noNamespaceSchemaLocation': "http://service-spi.web.cern.ch/service-spi/app/releases/GDML/schema/gdml.xsd"
#})
    gdml = ET.Element('gdml')
    define = ET.SubElement(gdml, 'define')
    materials = ET.SubElement(gdml, 'materials')
    solids = ET.SubElement(gdml, 'solids')
    structure = ET.SubElement(gdml, 'structure')
    setup = ET.SubElement(gdml, 'setup', {'name': 'Default', 'version': '1.0'})
    worldVOL = ET.SubElement(setup, 'world', {'ref': 'worldVOL'})
    #ET.ElementTree(gdml).write("test2", 'utf-8', True)


def defineMaterials():
    # Replaced by loading Default
    print("Define Materials")
    global materials
   
def defineWorldBox(exportList,bbox):
    for obj in exportList :
        # print("{} + {} = ".format(bbox, obj.Shape.BoundBox))
        if hasattr(obj,"Shape"):
           bbox.add(obj.Shape.BoundBox)
        if hasattr(obj,"Mesh"):
           bbox.add(obj.Mesh.BoundBox)
        if hasattr(obj,"Points"):
           bbox.add(obj.Points.BoundBox)
    #   print(bbox)
    # Solids get added to solids section of gdml ( solids is a global )
    ET.SubElement(solids, 'box', {'name': 'WorldBox',
                             'x': str(1000), \
                             'y': str(1000), \
                             'z': str(1000), \
                     #'x': str(2*max(abs(bbox.XMin), abs(bbox.XMax))), \
                     #'y': str(2*max(abs(bbox.YMin), abs(bbox.YMax))), \
                     #'z': str(2*max(abs(bbox.ZMin), abs(bbox.ZMax))), \
                     'lunit': 'mm'})


def constructWorld():
    print("Construct World")
    global worldVOL

    #ET.ElementTree(gdml).write("test9b", 'utf-8', True)
    # world volume needs to be added to structure after all other volumes
    worldVOL = ET.Element('volume', {'name': 'worldVOL'})
    ET.SubElement(worldVOL, 'materialref',{'ref': 'G4_Galactic'})
    ET.SubElement(worldVOL, 'solidref',{'ref': 'WorldBox'})
    # WorldBox is set in defineWorldBox
    #ET.SubElement(solids, 'box',{'name': 'WorldBox','x': '1000','y': '1000','z': '1000','lunit' : 'mm'})
    #ET.ElementTree(gdml).write("test9c", 'utf-8', True)

def createLVandPV(obj, name, solidName):
    #
    # Cannot rely on obj.Name so have to pass name
    # Logical & Physical Volumes get added to structure section of gdml
    #
    #ET.ElementTree(gdml).write("test9d", 'utf-8', True)
    #print("Object Base")
    #dir(obj.Base)
    #print dir(obj)
    #print dir(obj.Placement)
    global PVcount, POScount, ROTcount
    pvName = 'PV'+name+str(PVcount)
    PVcount += 1
    pos  = obj.Placement.Base
    lvol = ET.SubElement(structure,'volume', {'name':pvName})
    ET.SubElement(lvol, 'materialref', {'ref': 'SSteel0x56070ee87d10'})
    ET.SubElement(lvol, 'solidref', {'ref': solidName})
    # Place child physical volume in World Volume
    phys = ET.SubElement(worldVOL, 'physvol')
    ET.SubElement(phys, 'volumeref', {'ref': pvName})
    x = pos[0]
    y = pos[1]
    z = pos[2]
    if x!=0 and y!=0 and z!=0 :
       posName = 'Pos'+name+str(POScount)
       POScount += 1
       ET.SubElement(phys, 'position', {'name': posName, 'unit': 'mm', \
                  'x': str(x), 'y': str(y), 'z': str(y) })
    angles = obj.Placement.Rotation.toEuler()
    print ("Angles")
    print (angles)
    a0 = angles[0]
    a1 = angles[1]
    a2 = angles[2]
    if a0!=0 and a1!=0 and a2!=0 :
       rotName = 'Rot'+name+str(ROTcount)
       ROTcount += 1
       ET.SubElement(phys, 'rotation', {'name': rotName, 'unit': 'deg', \
                  'x': str(-a2), 'y': str(-a1), 'z': str(-a0)})

def createAdjustedLVandPV(obj, name, solidName, delta):
    # Allow for difference in placement between FreeCAD and GDML
    adjObj = obj
    rot = FreeCAD.Rotation(obj.Placement.Rotation)
    adjObj.Placement.move(rot.multVec(delta))#.negative()
    createLVandPV(adjObj, name, solidName)

def reportObject(obj) :
    
    print("Report Object")
    print(obj)
    print("Name : "+obj.Name)
    print("Type : "+obj.TypeId) 
    if hasattr(obj,'Placement') :
       print("Placement")
       print("Pos   : "+str(obj.Placement.Base))
       print("axis  : "+str(obj.Placement.Rotation.Axis))
       print("angle : "+str(obj.Placement.Rotation.Angle))
    
    while switch(obj.TypeId) :

      ###########################################
      # FreeCAD GDML Parts                      #
      ###########################################
      if case("Part::FeaturePython") : 
         print("Part::FeaturePython")
         if hasattr(obj.Proxy,'Type'):
            print (obj.Proxy.Type)
            print (obj.Name)
         else :
            print("Not a GDML Feature")
            
         #print dir(obj)
         #print dir(obj.Proxy)
         #print("cylinder : Height "+str(obj.Height)+ " Radius "+str(obj.Radius))
         break
      ###########################################
      # FreeCAD Parts                           #
      ###########################################
      if case("Part::Sphere") :
         print("Sphere Radius : "+str(obj.Radius))
         break
           
      if case("Part::Box") : 
         print("cube : ("+ str(obj.Length)+","+str(obj.Width)+","+str(obj.Height)+")")
         break

      if case("Part::Cylinder") : 
         print("cylinder : Height "+str(obj.Height)+ " Radius "+str(obj.Radius))
         break
   
      if case("Part::Cone") :
         print("cone : Height "+str(obj.Height)+ " Radius1 "+str(obj.Radius1)+" Radius2 "+str(obj.Radius2))
         break

      if case("Part::Torus") : 
         print("Torus")
         print(obj.Radius1)
         print(obj.Radius2)
         break

      if case("Part::Prism") :
         print("Prism")
         break

      if case("Part::RegularPolygon") :
         print("RegularPolygon")
         break

      if case("Part::Extrusion") :
         print("Extrusion")
         break

      if case("Circle") :
         print("Circle")
         break

      if case("Extrusion") : 
         print("Wire extrusion")
         break

      if case("Mesh::Feature") :
         print("Mesh")
         #print dir(obj.Mesh)
         break


      print("Other")
      print(obj.TypeId)
      break

def processPlanar(obj, shape, name ) :
    print ('Polyhedron ????')
    global defineCnt
    #
    print("Add tessellated Solid")
    tess = ET.SubElement(solids,'tessellated',{'name': name})
    print("Add Vertex positions")
    for f in shape.Faces :
       baseVrt = defineCnt
       for vrt in f.Vertexes :
           vnum = 'v'+str(defineCnt)
           ET.SubElement(define, 'position', {'name': vnum, \
              'x': str(vrt.Point.x), \
              'y': str(vrt.Point.y), \
              'z': str(vrt.Point.z), \
              'unit': 'mm'})
           defineCnt += 1
       print("Add vertex to tessellated Solid")
       vrt1 = 'v'+str(baseVrt)
       vrt2 = 'v'+str(baseVrt+1)
       vrt3 = 'v'+str(baseVrt+2)
       vrt4 = 'v'+str(baseVrt+3)
       NumVrt = len(f.Vertexes)
       if NumVrt == 3 :
          ET.SubElement(tess,'triangular',{ \
                      'vertex1': vrt1, \
                      'vertex2': vrt2, \
                      'vertex3': vrt3, \
                      'type': 'ABSOLUTE'})
       elif NumVrt == 4 :   
          ET.SubElement(tess,'quadrangular',{ \
                      'vertex1': vrt1, \
                      'vertex2': vrt2, \
                      'vertex3': vrt3, \
                      'vertex4': vrt4, \
                      'type': 'ABSOLUTE'})

def checkShapeAllPlanar(Shape) :
    for f in Shape.Faces :
        if f.Surface.isPlanar() == False :
           return False
        break
    return True

#    Add XML for TessellateSolid
def mesh2Tessellate(mesh, name) :
     global defineCnt

     baseVrt = defineCnt
     print ("mesh")
     print (mesh)
     print (dir(mesh))
     print ("Facets")
     print (mesh.Facets)
     print ("mesh topology")
     print (dir(mesh.Topology))
     print (mesh.Topology)
#
#    mesh.Topology[0] = points
#    mesh.Topology[1] = faces
#
#    First setup vertex in define section vetexs (points) 
     print("Add Vertex positions")
     for fc_points in mesh.Topology[0] : 
         print(fc_points)
         v = 'v'+str(defineCnt)
         ET.SubElement(define, 'position', {'name': v, \
                  'x': str(fc_points[0]), \
                  'y': str(fc_points[1]), \
                  'z': str(fc_points[2]), \
                  'unit': 'mm'})
         defineCnt += 1         
#                  
#     Add faces
#
     print("Add Triangular vertex")
     tess = ET.SubElement(solids,'tessellated',{'name': name})
     for fc_facet in mesh.Topology[1] : 
       print(fc_facet)
       vrt1 = 'v'+str(baseVrt+fc_facet[0])
       vrt2 = 'v'+str(baseVrt+fc_facet[1])
       vrt3 = 'v'+str(baseVrt+fc_facet[2])
       ET.SubElement(tess,'triangular',{ \
         'vertex1': vrt1, 'vertex2': vrt2 ,'vertex3': vrt3, 'type': 'ABSOLUTE'})


def processMesh(obj, Mesh, Name) :
    #  obj needed for Volune names
    #  object maynot have Mesh as part of Obj
    #  Name - allows control over name
    print("Create Tessellate Logical Volume")
    createLVandPV(obj, Name, 'Tessellated')
    mesh2Tessellate(Mesh, Name)
    return(Name)

def shape2Mesh(shape) :
     import MeshPart
     return (MeshPart.meshFromShape(Shape=shape, Deflection = 0.0))
#            Deflection= params.GetFloat('meshdeflection',0.0)) 

def processObjectShape(obj) :
    # Check if Planar
    # If plannar create Tessellated Solid with 3 & 4 vertex as appropriate
    # If not planar create a mesh and the a Tessellated Solid with 3 vertex
    print("Process Object Shape")
    print(obj)
    print(obj.PropertiesList)
    shape = obj.Shape
    print (shape)
    print(shape.ShapeType)
    while switch(shape.ShapeType) : 
      if case("Mesh::Feature") :
         print("Mesh - Should not occur should have been handled")
         #print("Mesh")
         #tessellate = mesh2Tessellate(mesh) 
         #return(tessellate)
         #break

         print("ShapeType Not handled")
         print(shape.ShapeType)
         break

#   Dropped through to here
#   Need to check has Shape

    print('Check if All planar')
    planar = checkShapeAllPlanar(shape)
    print(planar)

    if planar :
       return(processPlanar(obj,shape,obj.Name))

    else :
       # Create Mesh from shape & then Process Mesh
       #to create Tessellated Solid in Geant4
       return(processMesh(obj,shape2Mesh(shape),obj.Name))


def processBoxObject(obj, addVolsFlag) :
    # Needs unique Name
    boxName = 'Box' + obj.Name
    ET.SubElement(solids, 'box',{'name': boxName, \
                           'x': str(obj.Length.Value),  \
                           'y': str(obj.Width.Value),  \
                           'z': str(obj.Height.Value),  \
                           'lunit' : 'mm'})
    if addVolsFlag :
       # Adjustment for position in GDML
       delta = FreeCAD.Vector(obj.Length.Value / 2, \
                           obj.Width.Value / 2,  \
                           obj.Height.Value / 2)

       createAdjustedLVandPV(obj, obj.Name, boxName, delta)
    return(boxName)

def processCylinderObject(obj, addVolsFlag) :
    # Needs unique Name
    cylName = 'Cyl-' + obj.Name
    ET.SubElement(solids, 'tube',{'name': cylName, \
                           'rmax': str(obj.Radius.Value), \
                           'deltaphi': str(float(obj.Angle)), \
                           'aunit': 'deg',
                           'z': str(obj.Height.Value),  \
                           'lunit' : 'mm'})
    if addVolsFlag :
       # Adjustment for position in GDML
       delta = FreeCAD.Vector(0, 0, obj.Height.Value / 2)
       createAdjustedLVandPV(obj, obj.Name, cylName, delta)
    return(cylName)

def processConeObject(obj, addVolsFlag) :
    # Needs unique Name
    coneName = 'Cone' + obj.Name
    ET.SubElement(solids, 'cone',{'name': coneName, \
                           'rmax1': str(obj.Radius1.Value),  \
                           'rmax2': str(obj.Radius2.Value),  \
                           'deltaphi': str(float(obj.Angle)), \
                           'aunit': 'deg',
                           'z': str(obj.Height.Value),  \
                           'lunit' : 'mm'})
    if addVolsFlag :
       # Adjustment for position in GDML
       delta = FreeCAD.Vector(0, 0, obj.Height.Value / 2)
       createAdjustedLVandPV(obj, obj.Name, coneName, delta)
    return(coneName)

def processSection(obj, addVolsflag) :
    print("Process Section")
    ET.SubElement(solids, 'section',{'vertex1': obj.v1, \
            'vertex2': obj.v2, 'vertex3': obj.v3, 'vertex4': obj.v4, \
            'type': obj.vtype})


def processSphereObject(obj, addVolsFlag) :
    # Needs unique Name
    sphereName = 'Sphere' + obj.Name
    ET.SubElement(solids, 'sphere',{'name': sphereName, \
                           'rmax': str(obj.Radius.Value), \
                           'starttheta': str(90.-float(obj.Angle2)), \
                           'deltatheta': str(float(obj.Angle2-obj.Angle1)), \
                           'deltaphi': str(float(obj.Angle3)), \
                           'aunit': 'deg',
                           'lunit' : 'mm'})
    if addVolsFlag :
       createLVandPV(obj,obj.Name,sphereName)
    return(sphereName)

def processGDMLBoxObject(obj, addVolsFlag) :
    # Needs unique Name
    boxName = 'Box' + obj.Name
    ET.SubElement(solids, 'box',{'name': boxName, \
                           'x': str(obj.x.Value),  \
                           'y': str(obj.y.Value),  \
                           'z': str(obj.z.Value),  \
                           'lunit' : 'mm'})
    if addVolsFlag :
       # Adjustment for position in GDML
       delta = FreeCAD.Vector(obj.x.Value / 2, \
                           obj.y.Value / 2,  \
                           obj.z.Value / 2)
       createAdjustedLVandPV(obj, obj.Name, boxName, delta)
    return (boxName)

def processGDMLConeObject(obj, addVolsFlag) :
    # Needs unique Name
    coneName = 'Cone' + obj.Name
    ET.SubElement(solids, 'cone',{'name': coneName, \
                           'rmin1': str(obj.rmin1.Value),  \
                           'rmin2': str(obj.rmin2.Value),  \
                           'rmax1': str(obj.rmax1.Value),  \
                           'rmax2': str(obj.rmax2.Value),  \
                           'startphi': str(obj.startphi), \
                           'deltaphi': str(obj.deltaphi), \
                           'aunit': 'rad',
                           'z': str(obj.z.Value),  \
                           'lunit' : 'mm'})
    if addVolsFlag :
       # Adjustment for position in GDML
       delta = FreeCAD.Vector(0, 0, obj.z.Value / 2)
       createAdjustedLVandPV(obj, obj.Name, coneName, delta)
    return(coneName)

def processGDMLEllipsoidObject(obj, addVolsFlag) :
    # Needs unique Name
    ellipsoidName = 'Ellipsoid' + obj.Name
    ET.SubElement(solids, 'ellipsoid',{'name': ellipsoidName, \
                           'ax': str(obj.ax.Value),  \
                           'by': str(obj.by.Value),  \
                           'cz': str(obj.cz.Value),  \
                           'zcut1': str(obj.zcut1.Value),  \
                           'zcut2': str(obj.zcut2.Value),  \
                           'lunit' : 'mm'})
    if addVolsFlag :
       # Adjustment for position in GDML
       #delta = FreeCAD.Vector(0, 0, obj.z.Value / 2)
       delta = FreeCAD.Vector(0, 0, 0)
       createAdjustedLVandPV(obj, obj.Name, ellipsoidName, delta)
    return(ellipsoidName)

def processGDMLElTubeObject(obj, addVolsFlag) :
    # Needs unique Name
    eltubeName = 'Cone' + obj.Name
    ET.SubElement(solids, 'eltube',{'name': eltubeName, \
                           'dx': str(obj.dx.Value),  \
                           'dy': str(obj.dy.Value),  \
                           'dz': str(obj.dz.Value),  \
                           'lunit' : 'mm'})
    if addVolsFlag :
       # Adjustment for position in GDML
       delta = FreeCAD.Vector(0, 0, obj.dz.Value / 2)
       createAdjustedLVandPV(obj, obj.Name, eltubeName, delta)
    return(eltubeName)

def processGDMLPolyconeObject(obj, addVolsFlag) :
    # Needs unique Name
    #polyconeName = 'Cone' + obj.Name
    polyconeName = obj.Name
    ET.SubElement(solids, 'genericPolycone',{'name': polyconeName, \
                           'startphi': str(obj.startphi),  \
                           'deltaphi': str(obj.deltaphi),  \
                           'aunit': str(obj.aunit),  \
                           'lunit' : 'mm'})
    print(obj.OutList)
    for zplane in obj.OutList :
        ET.SubElement(solids, 'zplane',{'rmin': str(zplane.rmin), \
                               'rmax' : str(zplane.rmax), \
                               'z' : str(zplane.z)})

    if addVolsFlag :
       # Adjustment for position in GDML
       #delta = FreeCAD.Vector(0, 0, obj.dz.Value / 2)
       delta = FreeCAD.Vector(0, 0, 0)
       createAdjustedLVandPV(obj, obj.Name, polyconeName, delta)
    return(polyconeName)

def processGDMLQuadObject(obj, addVolsFlag) :
    print("GDMLQuadrangular")
    ET.SubElement(solids, 'quadrangular',{'vertex1': obj.v1, \
            'vertex2': obj.v2, 'vertex3': obj.v3, 'vertex4': obj.v4, \
            'type': obj.vtype})
    

def processGDMLSphereObject(obj, addVolsFlag) :
    # Needs unique Name
    sphereName = 'Sphere' + obj.Name
    ET.SubElement(solids, 'sphere',{'name': sphereName, \
                           'rmin': str(obj.rmin.Value),  \
                           'rmax': str(obj.rmax.Value),  \
                           'startphi': str(obj.startphi), \
                           'deltaphi': str(obj.deltaphi), \
                           'aunit': 'rad',
                           'lunit' : 'mm'})
    if addVolsFlag :
       createLVandPV(obj,obj.Name,sphereName)
    return(sphereName)

def processGDMLTessellatedObject(obj, addVolsFlag) :
    # Needs unique Name
    # Need to output unique define positions
    # Need to create set of positions
    #for items in obj.Outlist :
    #    ET.SubElement(GDMLShared.define,'position',{'name': obj.Name + 'v1', \
    #            'x':items.x , 'y':items.y, 'z':items.z,'unit':'mm')

    tessName = 'Tess' + obj.Name
    ET.SubElement(solids, 'tessellated',{'name': tessName})
    print(len(obj.OutList))
    for items in obj.OutList :
        if hasattr(items,'v4' ) :
            ET.SubElement(solids,'quadrangular',{'vertex1':'v1', \
                    'vertex2':'v2', 'vertex3':'v3', 'vertex4':'v4',
                                 'type':'ABSOLUTE'})
        else :    
            ET.SubElement(solids,'triangular',{'vertex1':'v1', 'vertex2':'v2', \
                                 'vertex3':'v3','type':'ABSOLUTE'})

    if addVolsFlag :
       # Adjustment for position in GDML
       delta = FreeCAD.Vector(0, 0, 0)
       createAdjustedLVandPV(obj, obj.Name, tessName, delta)
       return(tessName)


def processGDMLTrapObject(obj, addVolsFlag) :
    # Needs unique Name
    trapName = 'Trap' + obj.Name
    ET.SubElement(solids, 'trap',{'name': trapName, \
                           'z': str(obj.z.Value),  \
                           'theta': str(obj.theta),  \
                           'phi': str(obj.phi), \
                           'x1': str(obj.x1.Value),  \
                           'x2': str(obj.x2.Value),  \
                           'x3': str(obj.x3.Value),  \
                           'x4': str(obj.x4.Value),  \
                           'y1': str(obj.y1.Value),  \
                           'y2': str(obj.y2.Value),  \
                           'alpha1': str(obj.alpha), \
                           'alpha2': str(obj.alpha), \
                           'aunit': obj.aunit, \
                           'lunit': obj.lunit})
    if addVolsFlag :
       # Adjustment for position in GDML
       delta = FreeCAD.Vector(0, 0, obj.z.Value / 2)
       createAdjustedLVandPV(obj, obj.Name, trapName, delta)
    return(trapName)

def processGDMLTrdObject(obj, addVolsFlag) :
    # Needs unique Name
    trdName = 'Trd' + obj.Name
    ET.SubElement(solids, 'trd',{'name': trdName, \
                           'z': str(obj.z.Value),  \
                           'x1': str(obj.x1.Value),  \
                           'x2': str(obj.x2.Value),  \
                           'y1': str(obj.y1.Value),  \
                           'y2': str(obj.y2.Value),  \
                           'lunit': obj.lunit})
    if addVolsFlag :
       # Adjustment for position in GDML
       delta = FreeCAD.Vector(0, 0, obj.z.Value / 2)
       createAdjustedLVandPV(obj, obj.Name, trdName, delta)
    return(trdName)

def processGDMLTriangle(obj, addVolsFlag) :
    print("Process GDML Triangle")
    ET.SubElement(solids, 'triangular',{'vertex1': obj.v1, \
            'vertex2': obj.v2, 'vertex3': obj.v3,  \
            'type': obj.vtype})

def processGDMLTubeObject(obj, addVolsFlag) :
    # Needs unique Name
    tubeName = 'Tube' + obj.Name
    ET.SubElement(solids, 'tube',{'name': tubeName, \
                           'rmin': str(obj.rmin.Value),  \
                           'rmax': str(obj.rmax.Value),  \
                           'startphi': str(obj.startphi), \
                           'deltaphi': str(obj.deltaphi), \
                           'aunit': 'rad',
                           'z': str(obj.z.Value),  \
                           'lunit' : 'mm'})
    if addVolsFlag :
       # Adjustment for position in GDML
       delta = FreeCAD.Vector(0, 0, obj.z.Value / 2)
       createAdjustedLVandPV(obj, obj.Name, tubeName, delta)
    return(tubeName)

def processGDMLXtruObject(obj, addVolsFlag) :
    # Needs unique Name
    #tubeName = 'Tube' + obj.Name
    xtruName = obj.Name
    ET.SubElement(solids, 'xtru',{'name': xtruName, \
                           'lunit' : 'mm'})
    for items in obj.OutList :
        if items.Type == 'twoDimVertex' :
           ET.SubElement(solids, 'twoDimVertex',{'x': str(items.x), \
                                   'y': str(items.y)})
        if items.Type == 'section' :
           ET.SubElement(solids, 'section',{'zOrder': str(items.zOrder), \
                                  'zPosition': str(items.zPosition), \
                                  'xOffset' : str(items.xOffset), \
                                  'yOffset' : str(items.yOffset), \
                                  'scalingFactor' : str(items.scalingFactor)})


    if addVolsFlag :
       # Adjustment for position in GDML
       delta = FreeCAD.Vector(0, 0, 0)
       createAdjustedLVandPV(obj, obj.Name, xtruName, delta)
    return(xtruName)

def processGDML2dVertex(obj, addVolsFlag) :
    print("Process 2d Vertex")
    ET.SubElement(solids, 'twoDimVertex',{'x': obj.x, 'y': obj.y})


# Need to add position of object2 relative to object1
# Need to add rotation ??? !!!!
def addBooleanPositionAndRotation(element,obj1,obj2):
    print ("addBooleanPosition")
    print ("Position obj1")
    print (obj1.Placement.Base)
    print ("Position obj2")
    print (obj2.Placement.Base)
    global defineCnt
    positionName = 'Pos'+str(defineCnt)
    pos = obj2.Placement.Base - obj1.Placement.Base
    # Need to add rotation ??? !!!!
    ET.SubElement(define, 'position', {'name': positionName, \
            'x': str(pos[0]), 'y': str(pos[1]), 'z': str(pos[2]), \
            'unit': 'mm'})
    defineCnt += 1
    ET.SubElement(element,'positionref', {'ref': positionName})

def processGroup(obj, addVolsFlag) :
    print("Group Num : "+str(len(obj.Group)))
    for grp in obj.Group :
        processObject(grp, addVolsFlag)

def processElement(obj, item): # maybe part of material or element (common code)
    if hasattr(obj,'Z') :
       #print(dir(obj))
       item.set('Z',str(obj.Z)) 

    if hasattr(obj,'atom_unit') :
       atom = ET.SubElement(item,'atom') 
       atom.set('unit',str(obj.atom_unit)) 
            
       if hasattr(obj,'atom_value') :
          atom.set('value',str(obj.atom_value)) 

def processObject(obj, addVolsFlag) :
    print("\nProcess Object")
    global materials
    # return solid or boolean reference name
    # addVolsFlag = True then create Logical & Physical Volumes
    #             = False needed for booleans
    #ET.ElementTree(gdml).write("test9a", 'utf-8', True)
    while switch(obj.TypeId) :
      #
      # Deal with non solids
      #
      if case("App::DocumentObjectGroupPython"):
         print("   Object List : "+obj.Name)
         #print(obj)
         #print(dir(obj))
         global item
         while switch(obj.Name) :
            if case("Materials") : 
               print("Materials")
               break

            if case("Isotopes") :
               print("Isotopes")
               break
            
            if case("Elements") :
               print("Elements")
               break

            break
     
         if isinstance(obj.Proxy,GDMLconstant) :
            print("GDML constant")
            #print(dir(obj))

            item = ET.SubElement(define,'constant',{'name': obj.Name, \
                                 'value': obj.value })
            
         if isinstance(obj.Proxy,GDMLmaterial) :
            print("GDML material")
            #print(dir(obj))

            item = ET.SubElement(materials,'material',{'name': obj.Name})

            # process common options material / element
            processElement(obj, item)

            if hasattr(obj,'Dunit') :
               ET.SubElement(item,'D',{'unit': obj.Dunit, \
                                      'value': str(obj.Dvalue)})

            if hasattr(obj,'Tunit') :
               ET.SubElement(item,'T',{'unit': obj.Tunit, \
                                      'value': str(obj.Tvalue)})
           
            if hasattr(obj,'MEEunit') :
               ET.SubElement(item,'MEE',{'unit': obj.MEEunit, \
                                               'value': str(obj.MEEvalue)})

            break

         if isinstance(obj.Proxy,GDMLfraction) :

            print("GDML fraction")
            ET.SubElement(item,'fraction',{'n': str(obj.n), \
                                          'ref': obj.Name})
            break

         if isinstance(obj.Proxy,GDMLcomposite) :
            print("GDML Composite")
            break

         if isinstance(obj.Proxy,GDMLisotope) :
            print("GDML isotope")
            item = ET.SubElement(materials,'isotope',{'N': str(obj.N), \
                                                      'Z': str(obj.Z), \
                                                      'name' : obj.Name})
            ET.SubElement(item,'atom',{'unit': obj.unit, \
                                       'value': str(obj.value)})
            break

         if isinstance(obj.Proxy,GDMLelement) :
            print("GDML element")
            item = ET.SubElement(materials,'element',{'name': obj.Name})
            processElement(obj,item)
            break

         # Commented out as individual objects will also exist
         #if len(obj.Group) > 1 :
         #   for grp in obj.Group :
         #       processObject(grp, addVolsFlag)
         break

      if case("Part::Cut") :
         print("   Cut")
         cutName = 'Cut'+obj.Name
         ref1 = processObject(obj.Base,False)
         ref2 = processObject(obj.Tool,False)
         subtract = ET.SubElement(solids,'subtraction',{'name': cutName })
         ET.SubElement(subtract,'first', {'ref': ref1})
         ET.SubElement(subtract,'second',{'ref': ref2})
         addBooleanPositionAndRotation(subtract,obj.Base,obj.Tool)
         if addVolsFlag :
            createLVandPV(obj, obj.Name, cutName)
         return cutName
         break

      if case("Part::Fuse") :
         print("   Union")
         unionName = 'Union'+obj.Name
         ref1 = processObject(obj.Base,False)
         ref2 = processObject(obj.Tool,False)
         union = ET.SubElement(solids,'union',{'name': unionName })
         ET.SubElement(union,'first', {'ref': ref1})
         ET.SubElement(union,'second',{'ref': ref2})
         addBooleanPositionAndRotation(union,obj.Base,obj.Tool)
         #addPositionAndRotation(union,obj)
         if addVolsFlag :
            createLVandPV(obj, obj.Name, unionName)
         return unionName
         break

      if case("Part::Common") :
         print("   Intersection")
         intersectName = 'Intersect'+obj.Name
         ref1 = processObject(obj.Base,False)
         ref2 = processObject(obj.Tool,False)
         intersect = ET.SubElement(solids,'intersection',{'name': intersectName })
         ET.SubElement(intersect,'first', {'ref': ref1})
         ET.SubElement(intersect,'second',{'ref': ref2})
         addBooleanPositionAndRotation(intersect,obj.Base,obj.Tool)
         #addPositionAndRotation(intersect,obj)
         if addVolsFlag :
            createLVandPV(obj, obj.Name, intersectName)
         return intersectName
         break

      if case("Part::MultiFuse") :
         print("   Multifuse") 
         multName = 'MultiFuse'+obj.Name
         multUnion = ET.Element('multiUnion',{'name': multName })
         for subobj in obj.Shapes:
            solidName = processObject(subobj,False)
            node = ET.SubElement(multUnion,'multiUnionNode', \
               {'MF-Node' : 'Node-'+solidName})
            ET.SubElement(node,'solid', {'ref': solidName})
            addBooleanPositionAndRotation(node,subobj.Base,subobj.Tool)
            #addPositionAndRotation(node,subobj)
         solids.append(multUnion) 
         if addVolsFlag :
            createLVandPV(obj,obj.Name,multName)
         return multName
         break

      if case("Part::MultiCommon") :
         print("   Multi Common / intersection")
         print("   Not available in GDML")
         exit(-3)
         break

      if case("Mesh::Feature") :
         print("   Mesh Feature") 
         return(processMesh(obj, obj.Mesh, obj.Name))
         break

      if case("Part::FeaturePython"):
          print("   Python Feature")
          if hasattr(obj.Proxy, 'Type') :
             print(obj.Proxy.Type) 
             switch(obj.Proxy.Type)
             if case("GDMLBox") :
                print("      GDMLBox") 
                return(processGDMLBoxObject(obj, addVolsFlag))
                break

             if case("GDMLEllipsoid") :
                print("      GDMLEllipsoid") 
                return(processGDMLEllipsoidObject(obj, addVolsFlag))
                break

             if case("GDMLElTube") :
                print("      GDMLElTube") 
                return(processGDMLElTubeObject(obj, addVolsFlag))
                break

             if case("GDMLCone") :
                print("      GDMLCone") 
                return(processGDMLConeObject(obj, addVolsFlag))
                break

             if case("GDMLPolycone") :
                print("      GDMLPolycone") 
                return(processGDMLPolyconeObject(obj, addVolsFlag))
                break
             
             if case("GDMLSphere") :
                print("      GDMLSphere") 
                return(processGDMLSphereObject(obj, addVolsFlag))
                break

             if case("GDMLTessellated") :
                print("      GDMLTessellated") 
                return(processGDMLTessellatedObject(obj, addVolsFlag))
                break

             if case("GDMLTrap") :
                print("      GDMLTrap") 
                return(processGDMLTrapObject(obj, addVolsFlag))
                break

             if case("GDMLTrd") :
                print("      GDMLTrd") 
                return(processGDMLTrdObject(obj, addVolsFlag))
                break

             if case("GDMLTube") :
                print("      GDMLTube") 
                return(processGDMLTubeObject(obj, addVolsFlag))
                print("GDML Tube processed")
                break

             if case("GDMLXtru") :
                print("      GDMLXtru") 
                return(processGDMLXtruObject(obj, addVolsFlag))
                break

             print("Not yet Handled")

          else :
             print("Not a GDML Feature")
          break  
      # Same as Part::Feature but no position
      if case("App::FeaturePython") :
         print("App::FeaturePython") 
         # Following not needed as handled bu Outlist on Tessellated
         #if isinstance(obj.Proxy, GDMLQuadrangular) :
         #   return(processGDMLQuadObject(obj, addVolsFlag))
         #   break
  
         #if isinstance(obj.Proxy, GDMLTriangular) :
         #   return(processGDMLTriangleObject(obj, addVolsFlag))
         #   break
          
         # Following not needed as handled bu Outlist on Xtru

         #if isinstance(obj.Proxy, GDML2dVertex) :
         #   return(processGDML2dVertObject(obj, addVolsFlag))
         #   break
            
         #if isinstance(obj.Proxy, GDMLSection) :
         #   return(processGDMLSection(obj, addVolsFlag))
         #   break
         break  

      #
      #  Now deal with objects that map to GDML solids
      #
      if case("Part::Box") :
         print("    Box")
         return(processBoxObject(obj, addVolsFlag))
         break

      if case("Part::Cylinder") :
         print("    Cylinder")
         return(processCylinderObject(obj, addVolsFlag))
         break

      if case("Part::Cone") :
         print("    Cone")
         return(processConeObject(obj, addVolsFlag))
         break

      if case("Part::Sphere") :
         print("    Sphere")
         return(processSphereObject(obj, addVolsFlag))
         break

      # Not a Solid that translated to GDML solid
      # Dropped through so treat object as a shape
      # Need to check obj has attribute Shape
      # Create tessellated solid
      #
      #return(processObjectShape(obj, addVolsFlag))
      print("Convert FreeCAD shape to Tessellated")
      return(processObjectShape(obj))
      break

def export(exportList,filename) :
    "called when FreeCAD exports a file"
   
    # process Objects
    print("\nStart GDML Export 0.1")
    GDMLstructure()
    #defineMaterials()
    #constructWorld()
    bbox = FreeCAD.BoundBox()
    defineWorldBox(exportList, bbox)
    #for obj in exportList :
    zOrder = 1
    for obj in FreeCAD.ActiveDocument.Objects:
        #reportObject(obj)
        processObject(obj, True)

    # Now append World Volume definition to stucture
    # as it will contain references to volumes that need defining
    # before it
    structure.append(worldVOL)

    #ET.ElementTree(gdml).write("test9e", 'utf-8', True)

    # format & write GDML file 
    indent(gdml)
    print("Write to GDML file")
    #ET.ElementTree(gdml).write(filename, 'utf-8', True)
    ET.ElementTree(gdml).write(filename)
    print("GDML file written")
