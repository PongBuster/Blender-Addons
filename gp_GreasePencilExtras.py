bl_info = {
    "name": "Grease Pencil Extras",
    "author": "pongbuster",
    "version": (1, 3),
    "blender": (2, 90, 0),
    "location": "View3D > Sidebar (N)",
    "description": "A collection of utilities to align grease pencil stroke points and adjust stroke hardness.",
    "warning": "",
    "doc_url": "",
    "category": "Grease Pencil",
}

import bpy
import gpu
from bpy_extras import view3d_utils
from mathutils import Vector
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty

def get_selected_points(context):
    if context.active_object.type != 'GPENCIL':
        return []
    gp = context.active_object.data
    return [p
        for lr in gp.layers
            if not lr.lock and not lr.hide  #Respect layer locking and visibility
                for fr in ([fr for fr in lr.frames if fr.select or fr == lr.active_frame] if gp.use_multiedit else [lr.active_frame])    #Respect multiframe editing settings
                    for s in fr.strokes
                        if s.select
                            for p in s.points
                                if p.select]

def getPixel(X, Y):
    fb = gpu.state.active_framebuffer_get()
    screen_buffer = fb.read_color(X, Y, 1, 1, 3, 0, 'FLOAT')

    rgb_as_list = screen_buffer.to_list()[0]

    R = rgb_as_list[0][0]
    G = rgb_as_list[0][1]
    B = rgb_as_list[0][2]

    return R, G, B
    
class eyedropperOperator(bpy.types.Operator):
    """Left click to sample Fill color.
SHIFT-Left click to sample Stroke color.
"""

    bl_idname = "color.eyedropper"
    bl_label = "Color Eyedropper"
    bl_options = {'REGISTER' }
    
    @classmethod
    def poll(self, context):
        return (context.mode == 'PAINT_GPENCIL' or context.mode == 'VERTEX_GPENCIL')
    
    def modal(self, context, event):
        if event.type == "LEFTMOUSE":
            C = bpy.context

            if C.mode == 'VERTEX_GPENCIL':
                brush = C.tool_settings.gpencil_vertex_paint.brush
            else:
                brush = C.tool_settings.gpencil_paint.brush
                
            clr = getPixel(event.mouse_x, event.mouse_y)

            if event.shift == False:
                brush.gpencil_settings.vertex_mode = 'FILL' 
            else:
                brush.gpencil_settings.vertex_mode = 'STROKE'
                
            brush.color = clr

            context.window.cursor_modal_restore()
            return {'FINISHED'}
            
        return {'RUNNING_MODAL'}

    def execute(self, context):
        context.window.cursor_modal_set("EYEDROPPER")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class hardnessOperator(bpy.types.Operator):
    """Middle mouse to adjust selected strokes' hardness.
Hold CTRL to adjust selected points' pressure(radius) instead.
Hold SHIFT to adjust selected points' strength instead.
Left click to apply"""
    
    bl_idname = "stroke.hardness"
    bl_label = "Stroke Hardness"
    bl_options = {'REGISTER', 'UNDO'}
    selected_points = []
    @classmethod
    def poll(self, context):
        return (context.mode == 'SCULPT_GPENCIL' or context.mode == 'EDIT_GPENCIL')
    
    def modal(self, context, event):
        if event.type == "WHEELUPMOUSE" or event.type == "WHEELDOWNMOUSE":
            incr = -0.01 if event.type == "WHEELDOWNMOUSE" else 0.01

            if event.shift:
                incr *= 2
                for p in self.selected_points:
                    p.strength += incr
            elif event.ctrl:
                incr *= 10
                for p in self.selected_points:
                    p.pressure += incr
            else:
                gp =  context.active_object.data
                for lr in gp.layers:
                    if not lr.lock and not lr.hide:
                        frame_list = [fr for fr in lr.frames if fr.select] if gp.use_multiedit else [lr.active_frame]
                        for fr in frame_list:
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
        self.selected_points = get_selected_points(context)    
        context.window.cursor_modal_set("SCROLL_Y")
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        context.area.header_text_set(None)
        context.window.cursor_modal_restore()
    
class GPExtras_OT_set_stroke_property(bpy.types.Operator):
    """Sets the selected strokes' hardness, or the selected points' pressure or strength"""
    bl_idname = "gpextras.set_stroke_property"
    bl_label = "Set Stroke or Point Property"
    bl_options = {'REGISTER','UNDO'}

    value : FloatProperty(default=-1, min=0, name = "Value", description = "Amount to set the property to", options={'SKIP_SAVE'})
    mode : EnumProperty(items = [('HARDNESS', 'Hardness', "Strokes' Hardness"),
                                 ('LINE_WIDTH', 'Line Width', "Strokes' Line Width"),
                                 ('PRESSURE', 'Pressure', "Points' Pressure"), 
                                 ('STRENGTH', 'Strength', "Points' Strength")], name = "Mode", description = "Which property the operator should set", default = 'HARDNESS',options={'SKIP_SAVE'})
    linear_scale : BoolProperty(default=False, name = "Linear Scale", description = "Use linear values to set the stroke's hardness")
    
    @classmethod
    def description(cls, context, properties):
        match properties.mode:
            case 'HARDNESS':
                desc = "Sets the selected strokes' Hardness to " + ("the given value" if properties.value == -1 else str(int(properties.value))) + """.
Shift Click to use linear scaling for the hardness value"""
                
            case 'LINE_WIDTH':
                desc = "Sets the selected strokes' Line Width to " + ("the given value" if properties.value == -1 else str(int(properties.value)))
            case 'PRESSURE':
                desc = "Sets the selected points' Pressure(Thickness) to " + ("the given value" if properties.value == -1 else str(int(properties.value)))
            case 'STRENGTH':
                desc = "Sets the selected points' Strength(Transparency) to " + ("the given value" if properties.value == -1 else str(int(properties.value)))
            case _: #Default. Shouldn't happen, but you never know.
                desc = "Sets the selected strokes' hardness, or the selected points' pressure or strength"
        desc += """.
Alt Click to set to 1.
Control Click to set to 0"""
        return desc
    
    @classmethod
    def poll(self, context):
        return (context.mode == 'SCULPT_GPENCIL' or context.mode == 'EDIT_GPENCIL')

    def invoke(self, context, event):
        if event.alt:
            self.value = 1
        elif event.ctrl:
            self.value = 0
        elif self.value == -1:
            self.value = context.scene.gp_extras_stroke_prop_set_value
        if event.shift:
            self.linear_scale = True
        
        self.execute(context)
        return {'FINISHED'}
        
    def execute(self, context):
        match self.mode:
            case 'HARDNESS':
                gp =  context.active_object.data
                if self.value == 0 or self.value >= 1:
                    adjusted_value = self.value
                else:
                    try: 
                        adjusted_value = max(0, min(pow(self.value, 0.1) if self.linear_scale else self.value, 1))
                    except:
                        adjusted_value = 0
                for lr in gp.layers:
                    if not lr.lock and not lr.hide:
                        frame_list = [fr for fr in lr.frames if fr.select] if gp.use_multiedit else [lr.active_frame]
                        for fr in frame_list:
                            for s in fr.strokes:
                                if s.select:
                                    s.hardness = adjusted_value
            case 'LINE_WIDTH':
                gp =  context.active_object.data
                adjusted_value = int(self.value)    #Line Width needs to be an int
                for lr in gp.layers:
                    if not lr.lock and not lr.hide:
                        frame_list = [fr for fr in lr.frames if fr.select] if gp.use_multiedit else [lr.active_frame]
                        for fr in frame_list:
                            for s in fr.strokes:
                                if s.select:
                                    s.line_width = adjusted_value
            case 'PRESSURE':
                selected_points = get_selected_points(context)
                for p in selected_points:
                    p.pressure = self.value
            case 'STRENGTH':
                selected_points = get_selected_points(context)
                for p in selected_points:
                    p.strength = self.value
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        layout.prop(self, "mode")
        layout.prop(self, "value")
        if self.mode == 'HARDNESS':
            layout.prop(self, "linear_scale")
    

        

class mirrorOperator(bpy.types.Operator):
    arg: bpy.props.StringProperty()
    
    bl_idname = "stroke.mirror"
    bl_label = "Mirror Selection"
    bl_options = {'REGISTER', 'UNDO'}
    
    mirror : IntProperty(default=0)

    @classmethod
    def description(cls, context, properties):
        if properties.mirror == 1:
            txt = "Mirror vertically"
        else:
            txt = "Mirror horizontally"
        
        return txt

    @classmethod
    def poll(self, context):
        return (context.mode == 'SCULPT_GPENCIL' or context.mode == 'EDIT_GPENCIL')

    def execute(self, context):
        prev_mode = context.mode
        bpy.ops.object.mode_set(mode='EDIT_GPENCIL')
        if self.mirror == 0:
            bpy.ops.transform.mirror(orient_type='GLOBAL',
                orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                orient_matrix_type='GLOBAL',
                constraint_axis=(True, False, False))
        else:
            bpy.ops.transform.mirror(orient_type='GLOBAL',
                orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                orient_matrix_type='GLOBAL',
                constraint_axis=(False, False, True))
        bpy.ops.object.mode_set(mode=prev_mode)
            
        return {'FINISHED'}

class convergeOperator(bpy.types.Operator):
    arg: bpy.props.StringProperty()
    
    bl_idname = "stroke.converge"
    bl_label = "Converge Selection"
    bl_options = {'REGISTER', 'UNDO'}
    
    selectedPoint = None
    selected_points = []
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

        if event.type == "MOUSEMOVE":
            pos = view3d_utils.region_2d_to_location_3d(context.region, context.space_data.region_3d, 
                (event.mouse_region_x, event.mouse_region_y), (0,0,0))

            for p in self.selected_points:
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
                for p in self.selected_points:
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
        self.selected_points = get_selected_points(context)    
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
        context.scene.tool_settings.gpencil_selectmode_edit = 'POINT'    
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
        row.alignment = 'CENTER'
        # Converge selection
        row.operator('stroke.converge', icon = 'ANCHOR_CENTER', text = '' ).align = 0
        # Align Horizontally
        row.operator('stroke.converge', icon = 'ANCHOR_LEFT', text = '' ).align = 1
        # Align Vertically
        row.operator('stroke.converge', icon = 'ANCHOR_TOP', text = '' ).align = 2
        row.separator()
        # Mirror
        row.operator('stroke.mirror', icon = 'MOD_MIRROR', text = "").mirror = 0
        row.operator('stroke.mirror', icon = 'SNAP_EDGE', text = "").mirror = 1
        row.separator()
        # Sample
        row.operator('stroke.sample', icon = 'MOD_PARTICLE_INSTANCE', text = "")
        row.separator()
        # Eyedropper
        row.operator('color.eyedropper', icon = 'EYEDROPPER', text = "")
        box = layout.box()
        row = box.row(align=True)
        row.alignment = 'CENTER'
        # Cut Strokes
        row.operator('view3d.cutstroke_operator', icon = "SNAP_MIDPOINT", text = "" ) 
        row.separator()
        # Snapigon
        row.operator('stroke.snapigon', icon = "SNAP_ON", text = "" )
        row.separator()
        # Point Slide
        row.operator( 'object.pointslide_operator', icon='CON_TRACKTO', text='' )
        row.separator()
        # Hardness
        row.operator('stroke.hardness', icon = 'EVENT_H', text = "")
        row.separator()
        # Text
        row.operator("object.drawtext_operator", icon='EVENT_T', text='')
        # Set Stroke/Point Properties
        box = layout.box()
        row = box.row(align=True)
        row.prop(context.scene, "gp_extras_stroke_prop_set_value", text="")
        row.operator('gpextras.set_stroke_property', icon='MOD_OUTLINE',text = '').mode = 'HARDNESS'
        row.operator('gpextras.set_stroke_property', icon='STYLUS_PRESSURE',text = '',text_ctxt="Sets the selected points' pressure").mode = 'PRESSURE'
        row.operator('gpextras.set_stroke_property', icon='GP_MULTIFRAME_EDITING',text = '').mode = 'STRENGTH'

# Menu Additions
def gp_edit_gpencil_stroke_appends(self, context):
    props = self.layout.operator("gpextras.set_stroke_property", text = "Set Hardness")
    props.mode = 'HARDNESS'
    props.value = 1

# Class list to register
_classes = [
    eyedropperOperator,
    hardnessOperator,
    GPExtras_OT_set_stroke_property,
    convergeOperator,
    mirrorOperator,
    quickStrokeSampleOperator,
    PGP_PT_sidebarPanel
]
def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.gp_extras_stroke_prop_set_value = FloatProperty(default=0.5,min=0,max=300,name="Set Value",description="Value to set the selected strokes/points' hardness/pressure/strength to")
    bpy.types.VIEW3D_MT_edit_gpencil_stroke.append(gp_edit_gpencil_stroke_appends)
    
def unregister():
    del bpy.types.Scene.gp_extras_stroke_prop_set_value
    for cls in _classes:
        bpy.utils.unregister_class(cls)
        
if __name__ == "__main__":
    register()
