# DeltaWorks Blender addon: A mesh versioning tool that works on deltas
#    Copyright (C) 2021 Jerald Thomas
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see [http://www.gnu.org/licenses/].
#
# Also add information on how to contact you by electronic and paper mail.

from .util import *
from .props import *
from .ops import *

import bpy

import time

def draw_deltaworks_item(deltaworks_item, col):
    """Function that displays a deltaworks version information.
    Params:
        deltaworks_item: instance of PROP_DeltaWorksItem to be displayed
        col: Blender UILayout object
        
    Returns:
        None
    """
    
    row = col.row(align=True)
    row.label(text="Date Created:")
    row.label(text=time.strftime("%m/%d/%y %H:%M:%S", time.localtime(deltaworks_item.date)))
    
    row = col.row(align=True)
    row.label(text="Hash:")
    row.label(text=deltaworks_item.hash)
    
    row = col.row(align=True)
    row.label(text="Parent:")
    row.label(text=deltaworks_item.parent)
    
    row = col.row(align=True)
    row.label(text="Raw Size:")
    row.label(text=sizeof_fmt(deltaworks_item.raw_size))
    
    row = col.row(align=True)
    row.label(text="Delta Size:")
    row.label(text=sizeof_fmt(deltaworks_item.size))
    
    row = col.row(align=True)
    row.label(text="Verts/Edges/Faces:")
    row.label(text=f"{deltaworks_item.verts}/{deltaworks_item.edges}/{deltaworks_item.faces}")
    
    row = col.row(align=True)
    row.label(text="Description:")
    row = col.row(align=True)
    row.prop(deltaworks_item, "desc", text="", expand=True, emboss=True)

class DeltaWorksList(bpy.types.UIList):
    """A Blender UIList to display versions"""
    
    # Blender meta
    bl_idname = "DELTAWORKS_UL_DeltaWorksList"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        obj = data
        

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            selected_item = obj.deltaworks_list[obj.deltaworks_selected]
            
            if obj.deltaworks_settings.version_view == "LINEAGE":
                if not is_in_lineage(obj, selected_item.hash, item.hash):
                    return
            
            elif obj.deltaworks_settings.version_view == "CHILDREN":
                if selected_item.hash != item.hash and selected_item.hash != item.parent:
                    return
            
            if index == obj.deltaworks_cur:
                layout.label(text=time.strftime("%m/%d/%y", time.localtime(item.date)), icon="RADIOBUT_ON")
            else:
                layout.label(text=time.strftime("%m/%d/%y", time.localtime(item.date)), icon="RADIOBUT_OFF")
            
               
            layout.label(text=f"...{item.hash[-6:]}")

            
            layout.label(text=item.desc)
            
  
                
class DeltaWorksListPanel(bpy.types.Panel):
    """Panel that shows a list of all of the versions"""
    
    # Blender meta
    bl_label = "Versions List"
    bl_idname = "DELTAWORKS_PT_DeltaWorksListPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "DeltaWorks"

    def draw(self, context):
        obj = context.object
        if obj.deltaworks_cur < 0:
            return
        
        layout = self.layout
        deltaworks_item = obj.deltaworks_list[obj.deltaworks_selected]
        
        col = layout.column()
        
        col.prop(obj.deltaworks_settings, "version_view", text="View")
        
        row = col.row()
        row.label(text=f"{' ' * 10}Date")
        row.label(text="Hash")
        row.label(text="Description")

        col.template_list("DELTAWORKS_UL_DeltaWorksList", 
            "", 
            obj, 
            "deltaworks_list", 
            obj, 
            "deltaworks_selected", 
            #item_dyntip_propname="tooltip", 
            sort_lock=True)
        
        draw_deltaworks_item(deltaworks_item, col)
        
        col.separator(factor=2.0)
        
        row = col.row()
        row.operator("mesh.deltaworks_revert", icon="RECOVER_LAST", text="Revert")
        row.operator("mesh.deltaworks_delete", icon="X", text="Delete")
        row.enabled = (obj.mode == "OBJECT") and (obj.deltaworks_selected != obj.deltaworks_cur)


class DeltaWorksCurrentPanel(bpy.types.Panel):
    """Panel that shows information of the current version"""
    
    # Blender meta
    bl_label = "Current Version"
    bl_idname = "DELTAWORKS_PT_DeltaWorksCurrentPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DeltaWorks"
    
    def draw(self, context):
        obj = context.object
        if obj.deltaworks_cur < 0:
            return
        
        layout = self.layout
        deltaworks_item = obj.deltaworks_list[obj.deltaworks_cur]
        
        col = layout.column()
        
        draw_deltaworks_item(deltaworks_item, col)


class DeltaWorksNewPanel(bpy.types.Panel):
    """Panel where a new version can be created"""
    
    # Blender meta
    bl_label = "Create New Version"
    bl_idname = "DELTAWORKS_PT_DeltaWorksNewPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DeltaWorks"
    
    def draw(self, context):
        obj = context.object
        layout = self.layout
        
        layout.prop(obj.deltaworks_item, "desc", text="Description")
        
        layout.separator(factor=2.0)
        
        layout.operator("mesh.deltaworks_new", icon="DUPLICATE", text="Create New Version")
        
        layout.enabled = (isinstance(obj.data, bpy.types.Mesh) and obj.mode == "OBJECT")


class DeltaWorksSettingsPanel(bpy.types.Panel):
    """Panel where changes to the DeltaWorks settings can be made"""
    
    # Blender meta
    bl_label = "Settings"
    bl_idname = "DELTAWORKS_PT_DeltaWorksSettingsPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DeltaWorks"
    
    def draw(self, context):
        obj = context.object
        layout = self.layout
        
        row = layout.row()
        row.prop(obj.deltaworks_tmpsettings, "storage", text="Storage Type")
        
        row = layout.row()
        row.prop(obj.deltaworks_tmpsettings, "external_location", text="External Location")
        row.enabled = (obj.deltaworks_tmpsettings.external_location != "PACKED")
        
        row = layout.row()
        row.prop(obj.deltaworks_tmpsettings, "compression_value", text="Compression Value", slider=True)
        
        layout.separator(factor=2.0)
        
        row = layout.row()
        row.operator("mesh.deltaworks_settings_apply", icon="CHECKMARK", text="Apply")
        row.operator("mesh.deltaworks_settings_cancel", icon="X", text="Cancel")
