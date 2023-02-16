bl_info = {
    "name": "Grease Pencil Extras",
    "author": "pongbuster",
    "version": (1, 0),
    "blender": (2, 90, 0),
    "location": "View3D > Sidebar (N)",
    "description": "A collection of utilities to align grease pencil stroke points and adjust stroke hardness.",
    "warning": "",
    "doc_url": "",
    "category": "Grease Pencil",
}

import bpy
from bpy_extras import view3d_utils
from mathutils import Vector
from bpy.props import IntProperty

selected_points = []

def init_selected(context):
    gp = context.active_object
    
    if gp.type != 'GPENCIL':
        return
    
    selected_points.clear()
    
    for lr in gp.data.layers:
        for fr in lr.frames:
            if fr.frame_number == context.scene.frame_current:
                for s in fr.strokes:
                    for p in s.points:
                        if p.select:
                            selected_points.append(p)

class hardnessOperator(bpy.types.Operator):
    """Middle mouse to adjust selected Strokes' hardness.
Hold CTRL to adjust radius/strength.
Hold SHIFT to adjust pressure.
Left click to apply.
"""
    
    bl_idname = "stroke.hardness"
    bl_label = "Stroke Hardness"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(self, context):
        return (context.mode == 'SCULPT_GPENCIL' or context.mode == 'EDIT_GPENCIL')
    
    def modal(self, context, event):
        global selected_points
        
        if event.type == "WHEELUPMOUSE" or event.type == "WHEELDOWNMOUSE":
            incr = -0.01 if event.type == "WHEELDOWNMOUSE" else 0.01

            if event.shift:
                incr *= 2
                for p in selected_points:
                    p.strength += incr
            elif event.ctrl:
                incr *= 100
                for p in selected_points:
                    p.pressure += incr
            else:    
                for lr in context.active_object.data.layers:
                    for fr in lr.frames:
                        if fr.frame_number == context.scene.frame_current:
                            for s in fr.strokes:
                                if s.select:
                                    s.hardness += incr
                                    context.area.header_text_set("Hardness: %.4f" % s.hardness)
                    
        elif event.type == "LEFTMOUSE":
            context.area.header_text_set(None)
            context.window.cursor_modal_restore()
            return {'FINISHED'}
        
        return {'RUNNING_MODAL'}    

    def execute(self, context):
        init_selected(context)    
        context.window.cursor_modal_set("SCROLL_Y")
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}

class convergeOperator(bpy.types.Operator):
    arg: bpy.props.StringProperty()
    
    bl_idname = "stroke.converge"
    bl_label = "Converge Selection"
    bl_options = {'REGISTER', 'UNDO'}
    
    selectedPoint = None
    align : IntProperty(default=0)

    @classmethod
    def description(cls, context, properties):
        txt = "Converge"
        
        if properties.align == 1:
            txt = "Align horizontally"
        elif properties.align == 2:
            txt = "Align vertically"
        
        txt += """ selected points to the closest selected point from mouse.
Left click to apply. Right click to cancel.
        """
        
        return txt

    @classmethod
    def poll(self, context):
        return (context.mode == 'SCULPT_GPENCIL' or context.mode == 'EDIT_GPENCIL')
    
    def modal(self, context, event):
        global selected_points

        if event.type == "MOUSEMOVE":
            pos = view3d_utils.region_2d_to_location_3d(context.region, context.space_data.region_3d, 
                (event.mouse_region_x, event.mouse_region_y), (0,0,0))

            for p in selected_points:
                v = Vector((pos[0] - p.co[0], 0, pos[2] - p.co[2]))
                self.selectedPoint = None
                if v.length < 0.04:
                    self.selectedPoint = p
                    break
                
            if self.selectedPoint:
               context.window.cursor_modal_set("CROSSHAIR")
            else:
                context.window.cursor_modal_set("PAINT_CROSS")

        elif event.type == "LEFTMOUSE":
            context.window.cursor_modal_restore()
            context.window.cursor_modal_restore()

            if self.selectedPoint:
                for p in selected_points:
                    if self.align == 0 or self.align == 1:
                        p.co[0] = self.selectedPoint.co[0]
                    if self.align == 0 or self.align == 2:
                        p.co[2] = self.selectedPoint.co[2]
                    
                return {'FINISHED'}
            return {'CANCELLED'}
            
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            context.window.cursor_modal_restore()

            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}    
    
    def execute(self, context):
        init_selected(context)    
        context.window.cursor_modal_set("PAINT_CROSS")
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}

g_sample_length = 0.01

class quickStrokeSampleOperator(bpy.types.Operator):
    """
    Sample selected stroke with new points. Scroll mouse wheel to add / remove number of points.
    Hold shift for higher detail. Left click to apply. Right click to cancel.
    """
    
    bl_idname = "stroke.sample"
    bl_label = "Sample Stroke"
    bl_options = {'REGISTER', 'UNDO'}

    sample_interval = 0.05
    sample_length_bak = g_sample_length
    
    @classmethod
    def poll(self, context):
        return (context.mode == 'SCULPT_GPENCIL' or context.mode == 'EDIT_GPENCIL')
    
    def modal(self, context, event):
        global g_sample_length

        if event.shift:
            self.sample_interval = 0.001
        else:
            self.sample_interval = 0.01

        if event.type == 'WHEELUPMOUSE':
            if g_sample_length - self.sample_interval > 0:
                g_sample_length -= self.sample_interval
            context.area.header_text_set("Sample Length: %.4f" % g_sample_length)
            bpy.ops.gpencil.stroke_sample(length=g_sample_length)

        elif event.type == 'WHEELDOWNMOUSE':
            g_sample_length += self.sample_interval
            context.area.header_text_set("Sample Length: %.4f" % g_sample_length)
            bpy.ops.gpencil.stroke_sample(length=g_sample_length)

        elif event.type == "LEFTMOUSE":
            context.area.header_text_set(None)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            g_sample_length = self.sample_length_bak
            context.area.header_text_set(None)
            bpy.ops.ed.undo()
            return {'CANCELLED'}
       
        return {'RUNNING_MODAL'}    
    
    def execute(self, context):
        global g_sample_length
        
        context.area.header_text_set("Sample Length: %.4f" % g_sample_length)
            
        context.tool_settings.use_gpencil_select_mask_stroke=False
        context.tool_settings.use_gpencil_select_mask_point=True

        bpy.ops.gpencil.stroke_sample(length=g_sample_length)
        
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}
    
class PGP_PT_sidebarPanel(bpy.types.Panel):
    bl_label = "Grease Pencil Extras"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Grease Pencil"

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        row = box.row(align=True)
        col = row.column()
        # Converge selection
        col.operator('stroke.converge', icon = 'ANCHOR_CENTER', text = '' ).align = 0
        col = row.column()
        # Align Horizontally
        col.operator('stroke.converge', icon = 'ANCHOR_LEFT', text = '' ).align = 1
        col = row.column()
        # Align Vertically
        col.operator('stroke.converge', icon = 'ANCHOR_TOP', text = '' ).align = 2
        
        row.separator()
        row.separator()
        col = row.column()
        col.operator('stroke.sample', icon = 'EVENT_S', text = "")
        col = row.column()
        col.operator('stroke.hardness', icon = 'EVENT_H', text = "")

# Class list to register
_classes = [
    hardnessOperator,
    convergeOperator,
    quickStrokeSampleOperator,
    PGP_PT_sidebarPanel
]
def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    
def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    
def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
        
if __name__ == "__main__":
    register()
