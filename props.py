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

import bpy

class PROP_DeltaWorksItem(bpy.types.PropertyGroup):
    """PropertyGroup dataclass to store deltaworks version information"""
    
    date: bpy.props.IntProperty(name="Date", default=0)
    hash: bpy.props.StringProperty(name="Hash", default=f"{'0' * 32}")
    parent: bpy.props.StringProperty(name="Parent", default="")
    desc: bpy.props.StringProperty(name="Description", default="")
    size: bpy.props.IntProperty(name="Delta Size", default=0)
    raw_size:bpy.props.IntProperty(name="Raw Size", default=0)
    delta: bpy.props.StringProperty(name="Delta", default="")
    tooltip: bpy.props.StringProperty(name="Tooltip", default="My tooltip")
    verts: bpy.props.IntProperty(name="Verts", default=0)
    edges: bpy.props.IntProperty(name="Edges", default=0)
    faces: bpy.props.IntProperty(name="Faces", default=0)
    
class PROP_DeltaWorksSettings(bpy.types.PropertyGroup):
    """PropertyGroup dataclass to store deltaworks settings"""
    
    version_view: bpy.props.EnumProperty(name="View",
        items=[
            ("ALL", "All", "All versions will be shown", "", 1),
            ("LINEAGE", "Lineage", "All versions in the selected version's lineage will be shown", "", 2),
            ("CHILDREN", "Children", "Only the selected version and its direct children will be shown", "", 3),
        ],
        default="ALL",
        description = "Which versions to show with respect to the selected version")
        
    storage: bpy.props.EnumProperty(name="Storage",
        items=[
            ("PACKED", "Packed", "Deltas will be stored in the .blend file", "", 1),
            ("EXTERNAL", "External", "Deltas will be stored in an external location", "", 2)
        ],
        default="PACKED",
        description="Where the deltas are stored")
        
    external_location: bpy.props.StringProperty(name="External Location", 
        default=deltaworks_home+"deltas/", 
        subtype="DIR_PATH",
        description="Location of external delta files")
    
    compression_value: bpy.props.IntProperty(name="Compression Value", 
        default=9, 
        min=0, 
        max=9,
        description="How much compression to apply (less is faster but larger deltas)")
