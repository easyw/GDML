# GDML wrkbench gui init module
#
# Gathering all the information to start FreeCAD
# This is the second one of three init scripts, the third one
# runs when the gui is up

#***************************************************************************
#*   (c) Juergen Riegel (juergen.riegel@web.de) 2002                       *
#*                                                                         *
#*   This file is part of the FreeCAD CAx development system.              *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   FreeCAD is distributed in the hope that it will be useful,            *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Lesser General Public License for more details.                   *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with FreeCAD; if not, write to the Free Software        *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#*   Juergen Riegel 2002                                                   *
#*                                                                         *
#* Also copyright Keith Sloan                                              * 
#***************************************************************************/

#import FreeCAD
from FreeCAD import *
import PartGui
import GDMLCommands, GDMLResources
import gdml_locator, os, sys
global GDML_WB_icons_path
GDML_WBpath = os.path.dirname(gdml_locator.__file__)
GDML_WB_icons_path =  os.path.join( GDML_WBpath, 'Resources', 'icons')
GDML_WB_resources_path =  os.path.join( GDML_WBpath, 'Resources')

class GDML_Workbench ( Workbench ):

    class MyObserver():
       def __init__(self):
           self.signal = []

       def slotCreatedDocument(self, doc):
           import os, sys
           global GDML_WB_resources_path
           from importGDML import processGDML
           processGDML(doc,os.path.join(GDML_WB_resources_path,'Default.gdml'))
           # FreeCAD.getResourceDir() + \
           #             "Mod/GDML/Resources/Default.gdml")
    
    "GDML workbench object"
    def __init__(self):
        #self.__class__.Icon = FreeCAD.getResourceDir() + "Mod/GDML/Resources/icons/GDMLWorkbench.svg"
        import os, sys
        global GDML_WB_icons_path
        self.__class__.Icon = os.path.join(GDML_WB_icons_path, 'GDMLWorkbench.svg')
        self.__class__.MenuText = "GDML"
        self.__class__.ToolTip = "GDML workbench"

    def Initialize(self):
        global GDML_WB_icons_path, GDML_WB_resources_path
        def QT_TRANSLATE_NOOP(scope, text):
            return text
        
        #import GDMLCommands, GDMLResources
        commands=['CycleCommand','BoxCommand','ConeCommand','ElTubeCommand', \
                  'EllipsoidCommand','SphereCommand', \
                  'TrapCommand','TubeCommand']
        toolbarcommands=['CycleCommand','BoxCommand','ConeCommand', \
                         'ElTubeCommand', 'EllipsoidCommand','SphereCommand', \
                         'TrapCommand','TubeCommand']

        parttoolbarcommands = ['Part_Cut','Part_Fuse','Part_Common']

        self.appendToolbar(QT_TRANSLATE_NOOP('Workbench','GDMLTools'),toolbarcommands)
        self.appendMenu('GDML',commands)
        self.appendToolbar(QT_TRANSLATE_NOOP('Workbech','GDML Part tools'),parttoolbarcommands)
        #ResourcePath = FreeCAD.getHomePath() + "Mod/GDML/Resources/"
        ResourcePath = GDML_WB_resources_path
        print("Resource Path : "+ResourcePath)
        #FreeCADGui.addIconPath(FreeCAD.getResourceDir() + \
        #FreeCADGui.addIconPath(":/icons")
        FreeCADGui.addIconPath(GDML_WB_icons_path) 
        #FreeCADGui.addIconPath(ResourcePath + "icons")
        #FreeCADGui.addLanguagePath(":/translations")
        FreeCADGui.addLanguagePath(ResourcePath + "/translations")
        FreeCADGui.addPreferencePage(ResourcePath + "/ui/GDML-base.ui","GDML")

    def Activated(self):
        "This function is executed when the workbench is activated"
        print ("Activated")
        self.obs = self.MyObserver()
        App.addDocumentObserver(self.obs)
        return

    def Deactivated(self):
        "This function is executed when the workbench is deactivated"
        App.removeDocumentObserver(self.obs)
        return
    
    def GetClassName(self):
        return "Gui::PythonWorkbench"

Gui.addWorkbench(GDML_Workbench())

