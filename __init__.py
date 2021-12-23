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

bl_info = {
    "name": "DeltaWorks",
    "description": "A mesh versioning tool that works on deltas",
    "author": "Jerald Thomas",
    "version": (1, 0),
    "blender": (2, 90, 0),
    "warning": "This addon is still experimental",
    "support": "TESTING",
    "category": "Mesh",
}

from .util import *
from .ops import *
from .props import *
from .ui import *

import bpy

def register():
    
    # Props
    bpy.utils.register_class(PROP_DeltaWorksItem)
    bpy.utils.register_class(PROP_DeltaWorksSettings)
    
    # UI
    bpy.utils.register_class(DeltaWorksList)
    bpy.utils.register_class(DeltaWorksNewPanel)
    bpy.utils.register_class(DeltaWorksListPanel)
    bpy.utils.register_class(DeltaWorksCurrentPanel)
    bpy.utils.register_class(DeltaWorksSettingsPanel)
    
    # Operators
    bpy.utils.register_class(DeltaWorksRevertOperator)
    bpy.utils.register_class(DeltaWorksDeleteOperator)
    bpy.utils.register_class(DeltaWorksNewOperator)
    bpy.utils.register_class(DeltaWorksSettingsApplyOperator)
    bpy.utils.register_class(DeltaWorksSettingsCancelOperator)
    
    # Assign props to object types
    bpy.types.Object.deltaworks_list = bpy.props.CollectionProperty(type=PROP_DeltaWorksItem)
    bpy.types.Object.deltaworks_cur = bpy.props.IntProperty(default=-1)
    bpy.types.Object.deltaworks_selected = bpy.props.IntProperty(default=0)
    bpy.types.Object.deltaworks_item = bpy.props.PointerProperty(type=PROP_DeltaWorksItem)
    bpy.types.Object.deltaworks_settings = bpy.props.PointerProperty(type=PROP_DeltaWorksSettings)
    bpy.types.Object.deltaworks_tmpsettings = bpy.props.PointerProperty(type=PROP_DeltaWorksSettings)

def unregister():
    
    # Props
    bpy.utils.unregister_class(PROP_DeltaWorksItem)
    bpy.utils.unregister_class(PROP_DeltaWorksSettings)
    
    # UI
    bpy.utils.unregister_class(DeltaWorksList)
    bpy.utils.unregister_class(DeltaWorksNewPanel)
    bpy.utils.unregister_class(DeltaWorksListPanel)
    bpy.utils.unregister_class(DeltaWorksCurrentPanel)
    bpy.utils.unregister_class(DeltaWorksSettingsPanel)

    # Operators
    bpy.utils.unregister_class(DeltaWorksRevertOperator)
    bpy.utils.unregister_class(DeltaWorksDeleteOperator)
    bpy.utils.unregister_class(DeltaWorksNewOperator)
    bpy.utils.unregister_class(DeltaWorksSettingsApplyOperator)
    bpy.utils.unregister_class(DeltaWorksSettingsCancelOperator)

