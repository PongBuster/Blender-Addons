bl_info = {
    "name": "GPencil QuickTools",
    "author": "pongbuster",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > N sidebar",
    "description": "Adds grease pencil tool shortcuts to N sidebar",
    "warning": "",
    "doc_url": "",
    "category": "Grease Pencil",
}

import bpy
from bpy.props import StringProperty

class SetQuickToolOperator(bpy.types.Operator):
    arg: bpy.props.StringProperty()    
    """Tooltip"""
    bl_idname = "quicktools.set_quicktool"
    bl_label = ""

    args : StringProperty(default="")

    @classmethod
    def description(cls, context, properties):
        return "Set Brush to " + properties.args.split('|')[1]
            
    @classmethod
    def poll(cls, context):
        if context.active_object == None:
            return False
        return context.active_object.type == 'GPENCIL'

    def execute(self, context):
        mode, brush = self.args.split('|')

        if mode == 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        elif mode == 'JOIN':
            bpy.ops.gpencil.stroke_join(type='JOIN')
        elif mode == 'CLOSE':
            bpy.ops.gpencil.stroke_cyclical_set(type='CLOSE', geometry=True)
        else:
            bpy.ops.object.mode_set(mode=self.args.split('|')[0])
            bpy.ops.wm.tool_set_by_id(name=self.args.split('|')[1])

        return {'FINISHED'}

class QuickToolsPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "QuickTools"
    bl_idname = "OBJECT_PT_quicktools"

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Grease Pencil"
    
    def addOperator(self, ctool, row, op, tool_icon, parms):
        ptool = parms.split('|')[1]
        row.operator(op, depress = (ctool == ptool), icon = tool_icon).args = parms
        
    def draw(self, context):
        ctool = context.workspace.tools.from_space_view3d_mode(context.mode).idname

        layout = self.layout

        box = layout.box()
        box.operator("quicktools.set_quicktool", text = "OBJECT MODE").args = "OBJECT|MODE"
        row = box.row()
        row.operator("quicktools.set_quicktool", text = "JOIN").args = "JOIN|MODE"
        row.operator("quicktools.set_quicktool", text = "CLOSE").args = "CLOSE|MODE"
        
        box = layout.box()
        row = box.row()
        row = box.row()
        row.label(text='EDIT TOOLS')
        
        row = box.row(align=True)
        self.addOperator(ctool, row, "quicktools.set_quicktool", "RESTRICT_SELECT_OFF", "EDIT_GPENCIL|builtin.select_box")
#        row.operator("quicktools.set_quicktool", depress = (ctool == 'builtin.select_box'), icon = "RESTRICT_SELECT_OFF").args = "EDIT_GPENCIL|builtin.select_box"
        row.separator()
        self.addOperator(ctool, row, "quicktools.set_quicktool", "VIEW_PAN", "EDIT_GPENCIL|builtin.move")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "FILE_REFRESH", "EDIT_GPENCIL|builtin.rotate")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "MOD_LENGTH", "EDIT_GPENCIL|builtin.scale")
        row.separator()
        self.addOperator(ctool, row, "quicktools.set_quicktool", "MOD_OUTLINE", "EDIT_GPENCIL|builtin.radius")
        
        box = layout.box()
        row = box.row()
        row.label(text='DRAW TOOLS')
        row = box.row(align=True)
        self.addOperator(ctool, row, "quicktools.set_quicktool", "GPBRUSH_PENCIL", "PAINT_GPENCIL|builtin_brush.Draw")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "GPBRUSH_FILL", "PAINT_GPENCIL|builtin_brush.Fill")
        row.separator()
        self.addOperator(ctool, row, "quicktools.set_quicktool", "BRUSH_CURVES_CUT", "PAINT_GPENCIL|builtin.cutter")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "GPBRUSH_ERASE_STROKE", "PAINT_GPENCIL|builtin_brush.Erase")
        row.separator()
        self.addOperator(ctool, row, "quicktools.set_quicktool", "EYEDROPPER", "PAINT_GPENCIL|builtin.eyedropper")
        row = box.row(align=True)
        self.addOperator(ctool, row, "quicktools.set_quicktool", "IPO_LINEAR", "PAINT_GPENCIL|builtin.line")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "IPO_CONSTANT", "PAINT_GPENCIL|builtin.polyline")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "SPHERECURVE", "PAINT_GPENCIL|builtin.arc")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "IPO_EASE_OUT", "PAINT_GPENCIL|builtin.curve")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "MATPLANE", "PAINT_GPENCIL|builtin.box")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "ANTIALIASED", "PAINT_GPENCIL|builtin.circle")
        box = layout.box()
        row = box.row()
        row.label(text='SCULPT TOOLS')
        row = box.row(align=True)
        self.addOperator(ctool, row, "quicktools.set_quicktool", "GPBRUSH_SMOOTH", "SCULPT_GPENCIL|builtin_brush.Smooth")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "GPBRUSH_THICKNESS", "SCULPT_GPENCIL|builtin_brush.Thickness")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "GPBRUSH_STRENGTH", "SCULPT_GPENCIL|builtin_brush.Strength")
        row.separator()
        self.addOperator(ctool, row, "quicktools.set_quicktool", "GPBRUSH_PINCH", "SCULPT_GPENCIL|builtin_brush.Pinch")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "GPBRUSH_TWIST", "SCULPT_GPENCIL|builtin_brush.Twist")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "GPBRUSH_RANDOMIZE", "SCULPT_GPENCIL|builtin_brush.Randomize")
        row = box.row(align=True)
        self.addOperator(ctool, row, "quicktools.set_quicktool", "GPBRUSH_GRAB", "SCULPT_GPENCIL|builtin_brush.Grab")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "GPBRUSH_PUSH", "SCULPT_GPENCIL|builtin_brush.Push")

        box = layout.box()
        row = box.row()
        row.label(text='PAINT COLOR TOOLS')
        row = box.row(align=True)
        self.addOperator(ctool, row, "quicktools.set_quicktool", "GPBRUSH_PENCIL", "VERTEX_GPENCIL|builtin_brush.Draw")
        row.separator()
        self.addOperator(ctool, row, "quicktools.set_quicktool", "SCULPTMODE_HLT", "VERTEX_GPENCIL|builtin_brush.Blur")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "SCULPTMODE_HLT", "VERTEX_GPENCIL|builtin_brush.Average")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "SCULPTMODE_HLT", "VERTEX_GPENCIL|builtin_brush.Smear")
        row.separator()
        self.addOperator(ctool, row, "quicktools.set_quicktool", "GPBRUSH_MARKER", "VERTEX_GPENCIL|builtin_brush.Replace")
        
class quickToggleFullScreenOperator(bpy.types.Operator):
    bl_idname = "quick.togglefullscreen"    
    bl_label = "Quick Toggle FullScreen"
    
    def toggleFullScreen(self,context):
        if context.area:
            isFullScreen = context.window.width == context.area.width
        else:
            isFullScreen = True
            
        if not isFullScreen:
           context.window.cursor_modal_set("NONE")
        else:
           context.window.cursor_modal_restore()
        
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.view_perspective = 'CAMERA'
                override = {'screen' : context.screen, 'area' : area }
                with context.temp_override(**override):
                    bpy.ops.wm.window_fullscreen_toggle()
                    bpy.ops.screen.screen_full_area(use_hide_panels=True)

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == "WINDOW":
                        override = {'screen' : context.screen, 'area' : area, 'region' : region }
                        with context.temp_override(**override):
                            bpy.ops.view3d.view_center_camera()
                    
                for region in area.regions:
                    if region.type == "WINDOW":
                        for space in area.spaces:
                            if space.type == 'VIEW_3D':
                                override = {'screen' : context.screen, 'area' : area, 'region' : region, 'space' : space }
                                with context.temp_override(**override):
                                    bpy.context.space_data.overlay.show_overlays = isFullScreen
                                    bpy.context.space_data.show_gizmo = isFullScreen

    def modal(self, context, event):
        if event.type in {'ESC', 'LEFTMOUSE', 'RIGHTMOUSE'}:
            self.toggleFullScreen(context)
            return {'FINISHED'}
        
        return  {'PASS_THROUGH'}

    def execute(self, context):
        self.toggleFullScreen(context)
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'} 

# Class list to register
_classes = [
    SetQuickToolOperator,
    quickToggleFullScreenOperator,
    QuickToolsPanel
]

def menu_func(self, context):
    self.layout.operator(quickToggleFullScreenOperator.bl_idname, text=quickToggleFullScreenOperator.bl_label)
    
def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_view.append(menu_func)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_MT_view.remove(menu_func)

if __name__ == "__main__":
    register()
