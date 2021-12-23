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

from .dictdiffer import diff, patch

import bpy
import bmesh
from mathutils import Vector

import pickle
import zlib


deltaworks_home = bpy.utils.script_path_user() + "/addons/DeltaWorks/"


def sizeof_fmt(num, suffix="B"):
    """Makes a number human readable
    
    Source: https://stackoverflow.com/questions/1094841/get-human-readable-version-of-file-size
    """
    
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"
 
    
def bmvert_to_dict(bmvert):
    """Converts a bmvert datablock into a Python dictionary"""
    
    d = {}
    d["co"] = list(getattr(bmvert, "co"))
    d["hide"] = getattr(bmvert, "hide")
    d["index"] = getattr(bmvert, "index")
    d["normal"] = list(getattr(bmvert, "normal"))
    d["select"] = getattr(bmvert, "select")
    d["tag"] = getattr(bmvert, "tag")
        
    return d

def bmedge_to_dict(bmedge):
    """Converts a bmedge datablock into a Python dictionary"""
    
    d = {}
    d["hide"] = getattr(bmedge, "hide")
    d["index"] = getattr(bmedge, "index")
    d["seam"] = getattr(bmedge, "seam")
    d["select"] = getattr(bmedge, "select")
    d["smooth"] = getattr(bmedge, "smooth")
    d["tag"] = getattr(bmedge, "tag")
    d["verts"] = [x.index for x in list(getattr(bmedge, "verts"))]
    
    return d


def bmface_to_dict(bmface):
    """Converts a bmface datablock into a Python dictionary"""
    d = {}
    d["hide"] = getattr(bmface, "hide")
    d["index"] = getattr(bmface, "index")
    d["material_index"] = getattr(bmface, "material_index")
    d["normal"] = list(getattr(bmface, "normal"))
    d["select"] = getattr(bmface, "select")
    d["smooth"] = getattr(bmface, "smooth")
    d["tag"] = getattr(bmface, "tag")
    d["verts"] = [x.index for x in list(getattr(bmface, "verts"))]
    
    return d

def bmesh_to_dict(bm):
    """Converts a bmesh into a Python dictionary"""
    d = {}
    d["verts"] = sorted([bmvert_to_dict(bmvert) for bmvert in list(getattr(bm, "verts"))], key=lambda x: x["index"])
    d["edges"] = sorted([bmedge_to_dict(bmedge) for bmedge in list(getattr(bm, "edges"))], key=lambda x: x["index"])
    d["faces"] = sorted([bmface_to_dict(bmface) for bmface in list(getattr(bm, "faces"))], key=lambda x: x["index"])
    
    return d
    

def add_bmesh_verts(bm, verts):
    """Converts a Python dictionary into a list of bmverts and adds it to the provided bmesh"""
    
    vert_list = {}
    
    for vert in verts:
        bmvert = bm.verts.new(vert["co"])
        bmvert.hide = vert["hide"]
        bmvert.index = vert["index"]
        bmvert.normal = Vector(vert["normal"])
        bmvert.select = vert["select"]
        bmvert.tag = vert["tag"]
        
        vert_list[bmvert.index] = bmvert
        
    return vert_list
 
def add_bmesh_edges(bm, vert_list, edges):
    """Converts a Python dictionary into a list of bmedges and adds it to the provided bmesh"""
    
    for edge in edges:
        bmedge = bm.edges.new([vert_list[index] for index in edge["verts"]])
        bmedge.hide = edge["hide"]
        bmedge.index = edge["index"]
        bmedge.seam = edge["seam"]
        bmedge.select = edge["select"]
        bmedge.smooth = edge["smooth"]
        bmedge.tag = edge["tag"]
        
def add_bmesh_faces(bm, vert_list, faces):
    """Converts a Python dictionary into a list of bmfaces and adds it to the provided bmesh"""
    
    for face in faces:
        bmface = bm.faces.new([vert_list[index] for index in face["verts"]])
        bmface.hide = face["hide"]
        bmface.index = face["index"]
        bmface.material_index = face["material_index"]
        bmface.normal = Vector(face["normal"])
        bmface.select = face["select"]
        bmface.smooth = face["smooth"]
        bmface.tag = face["tag"]
    
def dict_to_bmesh(d, bm):
    """Converts a Python dictionary into the provided bmesh"""
    vert_list = add_bmesh_verts(bm, d["verts"])
    add_bmesh_edges(bm, vert_list, d["edges"])
    add_bmesh_faces(bm, vert_list, d["faces"])
    
    return bm


def build_bmesh_dict(obj, hash):
    """Builds a bmesh_dict of the version with the provided hash"""
    
    delta_items = list(obj.deltaworks_list)
    delta_hashes = [item.hash for item in delta_items]
    
    cur_item = delta_items[delta_hashes.index(hash)]
    
    items = [cur_item]
    
    while cur_item.parent != "":
        cur_item = delta_items[delta_hashes.index(cur_item.parent)]
        items.insert(0, cur_item)
    
    bmesh_dict = pickle.loads(zlib.decompress(get_delta_bytes(obj, items[0])))
    
    for item in items[1:]:
        patch(pickle.loads(zlib.decompress(get_delta_bytes(obj, item))), bmesh_dict, in_place=True)
        
    return bmesh_dict
    
def get_delta_bytes(obj, deltaworks_item):
    """Returns the delta in bytes form for the provided version item"""
    
    if obj.deltaworks_settings.storage == "PACKED":
        return bytes.fromhex(deltaworks_item.delta)
    
    else:
        p = pathlib.Path(obj.deltaworks_settings.external_location)
        f_name = f"{deltaworks_item.hash}.delta"
        
        return p.joinpath(f_name).read_bytes()
    
def set_delta_bytes(obj, deltaworks_item, delta_bytes):
    """Sets the delta in bytes form for the provided version item"""

    if obj.deltaworks_settings.storage == "PACKED":
        deltaworks_item.delta = delta_bytes.hex()
    
    else:
        p = pathlib.Path(obj.deltaworks_settings.external_location)
        f_name = f"{deltaworks_item.hash}.delta"
        p.joinpath(f_name).write_bytes(delta_bytes)
        
        deltaworks_item.delta = ""
        
def pack_deltas(obj):
    """Moves all deltas from an external location into the object datablock"""
    
    p = pathlib.Path(obj.deltaworks_settings.external_location)
    for item in obj.deltaworks_list:
        set_delta_bytes(obj, item, p.joinpath(f"{item.hash}.delta").read_bytes())
        p.joinpath(f"{item.hash}.delta").unlink()
        
def unpack_deltas(obj):
    """Moves all deltas from the object datablock to an external location"""
    
    p = pathlib.Path(obj.deltaworks_settings.external_location)
    p.mkdir(parents=True, exist_ok=True)
    for item in obj.deltaworks_list:
        p.joinpath(f"{item.hash}.delta").write_bytes(get_delta_bytes(obj, item))
        item.delta = ""
        
def is_in_lineage(obj, hash1, hash2):
    """Returns True if the versions represented by hash1 and hash2 share a common lineage and False otherwise"""
    delta_items = list(obj.deltaworks_list)
    delta_hashes = [item.hash for item in delta_items]
    
    # Check to see if they are the same
    if hash1 == hash2:
        return True
    
    # Check to see if hash2 is ancestor of hash1 
    cur_item = delta_items[delta_hashes.index(hash1)] 
    while cur_item.parent != "":
        if cur_item.parent == hash2:
            return True
        cur_item = delta_items[delta_hashes.index(cur_item.parent)]
           
    # Check to see if hash1 is ancestor of hash2
    cur_item = delta_items[delta_hashes.index(hash2)]
    while cur_item.parent != "":
        if cur_item.parent == hash1:
            return True
        cur_item = delta_items[delta_hashes.index(cur_item.parent)]    
        
    return False    
        
        
        
