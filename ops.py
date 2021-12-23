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
from .dictdiffer import diff

import bpy
import bmesh

import pickle
import zlib
import time
import hashlib
import pathlib


class DeltaWorksRevertOperator(bpy.types.Operator):
    """Revert to the selected version"""
    
    # Blender meta
    bl_idname = "mesh.deltaworks_revert"
    bl_label = "Revert"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        obj = context.object
        
        # Build selected version
        bmesh_dict = build_bmesh_dict(obj, obj.deltaworks_list[obj.deltaworks_selected].hash)
        
        # Set the object's mesh data to built version
        bm = dict_to_bmesh(bmesh_dict, bmesh.new())
        bm.to_mesh(obj.data)
        
        # Redraw the 3D View window
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        
        # Update cur to selected
        obj.deltaworks_cur = obj.deltaworks_selected
        
        return {"FINISHED"}

    
class DeltaWorksDeleteOperator(bpy.types.Operator):
    """Delete the selected version"""
    
    # Blender meta
    bl_idname = "mesh.deltaworks_delete"
    bl_label = "Delete"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        obj = context.object
        
        selected = obj.deltaworks_list[obj.deltaworks_selected]
        parent = build_bmesh_dict(obj, selected.parent)
        
        for item in obj.deltaworks_list:
            if item.parent == selected.hash:
                # Recalculate the delta for all children of selected
                child = build_bmesh_dict(obj, item.hash)
                delta = diff(parent, child)
                ser = pickle.dumps(list(delta))
                ser_comp = zlib.compress(ser, 9)
                new_hash = hashlib.md5(ser_comp).hexdigest().zfill(32)
                
                # Set the parent of all children of selected to selected's parent
                for item2 in obj.deltaworks_list:
                    if item2.parent == item.hash:
                        item2.parent = new_hash
                
                item.hash = new_hash
                set_delta_bytes(obj, item, ser_comp)
                item.size = len(ser_comp)
                item.parent = selected.parent
        
        # If last version is deleted, reset everything
        if len(obj.deltaworks_list) == 1:
            obj.property_unset("deltaworks_selected")
            obj.property_unset("deltaworks_cur")
            obj.deltaworks_list.clear()
            
        # Else, update cur and selected as required
        else:
            selected = obj.deltaworks_selected
            
            if obj.deltaworks_selected <= obj.deltaworks_cur:
                obj.deltaworks_cur -= 1
                
            if obj.deltaworks_selected == len(obj.deltaworks_list) - 1:
                obj.deltaworks_selected -= 1
                
            obj.deltaworks_list.remove(selected)
        
        return {"FINISHED"}

    
class DeltaWorksNewOperator(bpy.types.Operator):
    """Create a new version with the provided description"""
    
    # Blender meta
    bl_idname = "mesh.deltaworks_new"
    bl_label = "New"
    bl_options = {"REGISTER", "UNDO"}
    
    
    def execute(self, context):
        obj = context.object
        
        new_item = obj.deltaworks_list.add()
        
        new_item.date = time.time()
        new_item.desc = obj.deltaworks_item.desc
        
        if obj.deltaworks_cur >= 0:
            new_item.parent = obj.deltaworks_list[obj.deltaworks_cur].hash
            
            # build parent
            parent = build_bmesh_dict(obj, new_item.parent)
            
            # get diff of parent and self
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bmesh_dict = bmesh_to_dict(bm)
            delta = diff(parent, bmesh_dict)
            
            # serialize diff, compress, and store
            ser = pickle.dumps(list(delta))
            ser_comp = zlib.compress(ser, 9)
            new_item.hash = hashlib.md5(ser_comp).hexdigest().zfill(32)
            set_delta_bytes(obj, new_item, ser_comp)
            new_item.size = len(ser_comp)
            new_item.raw_size = len(zlib.compress(pickle.dumps(bmesh_dict), 9))
            
            # populate mesh info
            new_item.verts = len(bmesh_dict["verts"])
            new_item.edges = len(bmesh_dict["edges"])
            new_item.faces = len(bmesh_dict["faces"])           
            
            # free bmesh
            bm.free()
        
        else:
            # build dict
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bmesh_dict = bmesh_to_dict(bm)
            
            # populate mesh info
            new_item.verts = len(bmesh_dict["verts"])
            new_item.edges = len(bmesh_dict["edges"])
            new_item.faces = len(bmesh_dict["faces"])
            
            # serialize, compress, and store
            ser = pickle.dumps(bmesh_dict)
            ser_comp = zlib.compress(ser, 9)
            new_item.hash = hashlib.md5(ser_comp).hexdigest().zfill(32)
            set_delta_bytes(obj, new_item, ser_comp)
            new_item.size = len(ser_comp)
            new_item.raw_size = len(ser_comp)
            
            # free bmesh
            bm.free()


        obj.deltaworks_cur = list(obj.deltaworks_list).index(new_item)
        obj.deltaworks_selected = obj.deltaworks_cur

        obj.property_unset("deltaworks_item")
        return {"FINISHED"}
        
class DeltaWorksSettingsApplyOperator(bpy.types.Operator):
    """Apply changes to the settings"""
    
    # Blender meta
    bl_idname = "mesh.deltaworks_settings_apply"
    bl_label = "Apply"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        
        obj = context.object
        
        if obj.deltaworks_tmpsettings.storage != obj.deltaworks_settings.storage:
            if obj.deltaworks_settings.storage == "PACKED":
                unpack_deltas(obj)
            
            obj.deltaworks_settings.storage = obj.deltaworks_tmpsettings.storage
            
            if obj.deltaworks_settings.storage == "PACKED":
                pack_deltas(obj)
            
        if obj.deltaworks_tmpsettings.external_location != obj.deltaworks_settings.external_location:
            p_new = pathlib.Path(obj.deltaworks_tmpsettings.external_location)
            p_old = pathlib.Path(obj.deltaworks_settings.external_location)
            
            p_new.mkdir(parents=True, exist_ok=True)
            
            if obj.deltaworks_settings.storage == "EXTERNAL":
                for f in p_old.glob("*.delta"):
                    f.rename(p_new.joinpath(p.name))
            
            obj.deltaworks_settings.external_location = obj.deltaworks_tmpsettings.external_location
            
        if obj.deltaworks_tmpsettings.compression_value != obj.deltaworks_settings.compression_value:
            if obj.deltaworks_settings.storage == "PACKED":
                for item in obj.deltaworks_list:
                    ser = zlib.decompress(get_delta(obj, item))
                    ser_comp = zlib.compress(ser, obj.deltaworks_tmpsettings.compression_value)
                    set_delta_bytes(obj, item, ser_comp)
                    item.size = len(ser_comp)
            
            obj.deltaworks_settings.compression_value = obj.deltaworks_tmpsettings.compression_value
            
        return {"FINISHED"}
    

class DeltaWorksSettingsCancelOperator(bpy.types.Operator):
    """Cancel changes to the settings"""
    
    # Blender meta
    bl_idname = "mesh.deltaworks_settings_cancel"
    bl_label = "Cancel"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        
        obj = context.object
        
        for setting in obj.deltaworks_settings.__annotations__:
            setattr(obj.deltaworks_tmpsettings, setting, getattr(obj.deltaworks_settings, setting))
        
        
        return {"FINISHED"}
