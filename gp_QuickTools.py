bl_info = {
    "name": "GPencil QuickTools",
    "author": "pongbuster",
    "version": (1, 4),
    "blender": (2, 80, 0),
    "location": "View3D > N sidebar",
    "description": "Adds grease pencil tool shortcuts to N sidebar",
    "warning": "",
    "doc_url": "",
    "category": "Grease Pencil",
}

import bpy
from bpy.props import StringProperty

from bpy_extras import view3d_utils
from mathutils import Vector

def s2lin(x): # convert srgb to linear
    a = 0.055
    if x <= 0.04045:
        y = x * (1.0 /12.92)
    else:
        y = pow ( (x + a) * (1.0 / (1 + a)), 2.4)
    return y

class SetQuickToolOperator(bpy.types.Operator):
    arg: bpy.props.StringProperty()    
    """Tooltip"""
    bl_idname = "quicktools.set_quicktool"
    bl_label = ""

    args : StringProperty(default="")
    
    @classmethod
    def description(cls, context, properties):
        tooltips = dict(LINKED = 'Select all points on selected strokes',
            LAYER = 'Highlight layer selected stroke is on',
            FILL = "Set Vertex Replace color to selected strokes on the active keyframe",
        )

        args = properties.args.split('|')
        
        if tooltips.get(args[1]):
            return tooltips.get(args[1])

        return args[1]
            
    @classmethod
    def poll(cls, context):
        if context.active_object == None:
            return False
        return context.active_object.type == 'GPENCIL'

    def execute(self, context):
        mode, cmd = self.args.split('|')

        if mode == 'OPS':
            if cmd == 'OBJECTMODE':
                bpy.ops.object.mode_set(mode='OBJECT')
            elif cmd == 'JOIN':
                bpy.ops.gpencil.stroke_join(type='JOIN')
            elif cmd == 'CLOSE':
                bpy.ops.gpencil.stroke_cyclical_set(type='CLOSE', geometry=True)
            elif cmd == 'UNDO':
                try: bpy.ops.ed.undo()
                except: None
            elif cmd == 'REDO':
                try: bpy.ops.ed.redo()
                except: None
            elif cmd == 'FULLSCREEN':
                bpy.ops.quick.togglefullscreen()
            elif cmd == 'BOUNDS':
                bpy.ops.view3d.view_center_camera()

            elif cmd == 'BRING_TO_FRONT':
                bpy.ops.gpencil.stroke_arrange(direction='TOP')
            elif cmd == 'BRING_FORWARD':
                bpy.ops.gpencil.stroke_arrange(direction='UP')
            elif cmd == 'SEND_BACKWARD':
                bpy.ops.gpencil.stroke_arrange(direction='DOWN')
            elif cmd == 'SEND_TO_BACK':
                bpy.ops.gpencil.stroke_arrange(direction='BOTTOM')

            elif cmd == 'FRAME':
                gp = context.active_object

                if gp.type != 'GPENCIL':
                    return
                
                minx = miny = 9999
                maxx = maxy = -9999
                avg = Vector((0,0,0))
                
                for lr in gp.data.layers:
                    if lr.lock == True:
                        continue
                    if lr.hide == True:
                        continue                    
                    for fr in lr.frames:
                        if fr.frame_number == context.scene.frame_current:
                            for s in fr.strokes:
                                for p in s.points:
                                    if p.select:
                                        minx = min(minx, p.co[0])
                                        maxx = max(maxx, p.co[0])
                                        miny = min(miny, p.co[2])
                                        maxy = max(maxy, p.co[2])
                                        
                if minx == miny and maxx == maxy:
                    return {'FINISHED'}
                    
                center = Vector( ((maxx - minx) / 2 + minx, (maxy - miny) / 2 + miny) )
                
                r3d = context.space_data.region_3d

                r3d.view_camera_zoom = 0
                r3d.view_camera_offset[0] = center[0] / 18
                r3d.view_camera_offset[1] = center[1] / 8

                rw = (maxx - minx) / 8.668856
                rh = (maxy - miny) / 4.903836
                
                if (maxy - miny) > (maxx - minx):
                    rw = rh
                    
                if rw < 0.06:
                    rw = 0.06

                r3d.view_camera_zoom = 30 + 10 / rw
                    
            elif cmd == 'LAYER':
                if context.active_object.type != 'GPENCIL':
                    return
                gp = context.active_object
                for idx, lr in enumerate(gp.data.layers):
                    for fr in lr.frames:
                        if fr.frame_number == context.scene.frame_current:
                            for s in fr.strokes:
                                if s.select:
                                    gp.data.layers.active_index = idx
                                    break
                                
            elif cmd == 'FILL':
                gp = context.active_object
                clr = bpy.data.brushes['Vertex Replace'].color
                
                for lr in gp.data.layers:
                    for fr in lr.frames:
                        if fr.frame_number == context.scene.frame_current:
                            for s in fr.strokes:
                                for p in s.points:
                                    if p.select:
                                         s.vertex_color_fill = (s2lin(clr[0]), s2lin(clr[1]), s2lin(clr[2]), 1)


            elif cmd == 'EDIT_POINT':
                bpy.context.scene.tool_settings.gpencil_selectmode_edit = 'POINT'
            elif cmd == 'EDIT_STROKE':
                bpy.context.scene.tool_settings.gpencil_selectmode_edit = 'STROKE'
            elif cmd == 'SMOOTH':
                bpy.ops.object.mode_set(mode='EDIT_GPENCIL')
                bpy.context.scene.tool_settings.gpencil_selectmode_edit = 'POINT'
                bpy.ops.gpencil.stroke_smooth(only_selected=True)
            elif cmd == 'SUBDIVIDE':
                bpy.ops.gpencil.stroke_subdivide(only_selected=False)
            elif cmd == 'SCULPT_POINT':
                 bpy.context.scene.tool_settings.use_gpencil_select_mask_point = not bpy.context.scene.tool_settings.use_gpencil_select_mask_point
            elif cmd == 'SCULPT_STROKE':
                 bpy.context.scene.tool_settings.use_gpencil_select_mask_stroke = not bpy.context.scene.tool_settings.use_gpencil_select_mask_stroke
            elif cmd == 'LINKED':
                bpy.ops.gpencil.select_linked()
            else:
                print(cmd + " not handled")
        else:
            try:
                bpy.context.object.data.use_curve_edit = False
                bpy.ops.object.mode_set(mode=self.args.split('|')[0])
                bpy.ops.wm.tool_set_by_id(name=self.args.split('|')[1])
            except:
                None

        return {'FINISHED'}

class quickToggleFullScreenOperator(bpy.types.Operator):
    bl_idname = "quick.togglefullscreen"    
    bl_label = "Quick Toggle FullScreen"
    
    _timer = None

    def show(self, context, isFull):
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
                    bpy.ops.screen.screen_full_area(use_hide_panels=True)
                    bpy.ops.wm.window_fullscreen_toggle()

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == "WINDOW":
                        for space in area.spaces:
                            if space.type == 'VIEW_3D':
                                override = {'screen' : context.screen, 'area' : area, 'region' : region, 'space' : space }
                                with context.temp_override(**override):
                                    bpy.context.space_data.overlay.show_overlays = isFullScreen
                                    bpy.context.space_data.show_gizmo = isFullScreen
                                        
    def modal(self, context, event):
        if event.type == 'TIMER':
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    for region in area.regions:
                        if region.type == "WINDOW":
                            override = {'screen' : context.screen, 'area' : area, 'region' : region }
                            with context.temp_override(**override):
                                bpy.ops.view3d.view_center_camera()
            if self._timer:                    
                wm = context.window_manager
                wm.event_timer_remove(self._timer)
                self._timer = None
                        
        elif event.type in {'ESC', 'LEFTMOUSE', 'RIGHTMOUSE'} and not self._timer:
            self.show(context, True)
            return {'FINISHED'}

        return  {'PASS_THROUGH'}

    def execute(self, context):
        self.show(context, False)
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.2, window=context.window)
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'} 

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
        row = box.row()
        col = row.column()
        row = col.row(align=True)
        row.operator("quicktools.set_quicktool", text = "OBJECT MODE").args = "OPS|OBJECTMODE"
        
        col = row.column()
        row = col.row(align=True)
        row.separator()
        row.operator("quicktools.set_quicktool", icon = "ZOOM_ALL").args = "OPS|BOUNDS"
        row.operator("quicktools.set_quicktool", icon = "ZOOM_SELECTED").args = "OPS|FRAME"
        row.operator("quicktools.set_quicktool", icon = "FULLSCREEN_ENTER").args = "OPS|FULLSCREEN"
        
        row1 = layout.row()
        col = row1.column()
        box = col.box()
        row = box.row()

        row.operator("quicktools.set_quicktool", text = "UNDO").args = "OPS|UNDO"
#        row.separator()
        row.operator("quicktools.set_quicktool", text = "REDO").args = "OPS|REDO"

        row = box.row()
        row.operator("quicktools.set_quicktool", text = "JOIN").args = "OPS|JOIN"
        row.operator("quicktools.set_quicktool", text = "CLOSE").args = "OPS|CLOSE"
        
        col = row1.column()
        box = col.box()
        row = box.row()
        row.operator("quicktools.set_quicktool", icon = "SORT_DESC").args = "OPS|BRING_FORWARD"
        row.operator("quicktools.set_quicktool", icon = "EXPORT").args = "OPS|BRING_TO_FRONT"
        row = box.row()
        row.operator("quicktools.set_quicktool", icon = "SORT_ASC").args = "OPS|SEND_BACKWARD"
        row.operator("quicktools.set_quicktool", icon = "IMPORT").args = "OPS|SEND_TO_BACK"
        
        
        box = layout.box()
        row = box.row()
        row.label(text='EDIT TOOLS')
        
        row = box.row(align=True)
        self.addOperator(ctool, row, "quicktools.set_quicktool", "RESTRICT_SELECT_OFF", "EDIT_GPENCIL|builtin.select_box")
        row.separator()
        row.operator("quicktools.set_quicktool", icon = "PARTICLE_DATA").args = "OPS|LINKED"
#        row.operator("quicktools.set_quicktool", depress = (ctool == 'builtin.select_box'), icon = "RESTRICT_SELECT_OFF").args = "EDIT_GPENCIL|builtin.select_box"
        row.separator()

        selectmode = bpy.context.scene.tool_settings.gpencil_selectmode_edit
        row.operator("quicktools.set_quicktool", icon="GP_SELECT_POINTS", depress=selectmode=="POINT").args = "OPS|EDIT_POINT"
        row.operator("quicktools.set_quicktool", icon="GP_SELECT_STROKES", depress=selectmode=="STROKE").args = "OPS|EDIT_STROKE"
        row.separator()
        row.operator("quicktools.set_quicktool", icon="RENDERLAYERS").args = "OPS|LAYER"
        row.separator()
        row.operator("quicktools.set_quicktool", icon="VIEW_ORTHO").args = "OPS|SUBDIVIDE"

        row = box.row(align=True)
         
        self.addOperator(ctool, row, "quicktools.set_quicktool", "ARROW_LEFTRIGHT", "EDIT_GPENCIL|builtin.move")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "FILE_REFRESH", "EDIT_GPENCIL|builtin.rotate")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "MOD_LENGTH", "EDIT_GPENCIL|builtin.scale")
        row.separator()
        self.addOperator(ctool, row, "quicktools.set_quicktool", "OUTLINER_OB_GREASEPENCIL", "EDIT_GPENCIL|builtin.extrude")
        row.separator()
        self.addOperator(ctool, row, "quicktools.set_quicktool", "MOD_OUTLINE", "EDIT_GPENCIL|builtin.radius")
        row.separator()
        row.operator("quicktools.set_quicktool", icon="FCURVE", depress=bpy.context.object.data.use_curve_edit).args = "OPS|SMOOTH"
        
        box = layout.box()
        row = box.row()
        row.label(text='DRAW TOOLS')
        row = box.row(align=True)
        self.addOperator(ctool, row, "quicktools.set_quicktool", "GPBRUSH_PENCIL", "PAINT_GPENCIL|builtin_brush.Draw")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "GPBRUSH_FILL", "PAINT_GPENCIL|builtin_brush.Fill")
        row.separator()
        self.addOperator(ctool, row, "quicktools.set_quicktool", "MOD_TINT", "PAINT_GPENCIL|builtin_brush.Tint")
        row.separator()
        self.addOperator(ctool, row, "quicktools.set_quicktool", "BRUSH_CURVES_CUT", "PAINT_GPENCIL|builtin.cutter")
        row.separator()
        self.addOperator(ctool, row, "quicktools.set_quicktool", "GPBRUSH_ERASE_STROKE", "PAINT_GPENCIL|builtin_brush.Erase")
        row.separator()

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
        row.separator()
        selectmode = bpy.context.scene.tool_settings.use_gpencil_select_mask_point
        row.operator("quicktools.set_quicktool", icon="GP_SELECT_POINTS", depress=selectmode).args = "OPS|SCULPT_POINT"
        selectmode = bpy.context.scene.tool_settings.use_gpencil_select_mask_stroke
        row.operator("quicktools.set_quicktool", icon="GP_SELECT_STROKES", depress=selectmode).args = "OPS|SCULPT_STROKE"
        row.separator()
        self.addOperator(ctool, row, "quicktools.set_quicktool", "RESTRICT_SELECT_OFF", "SCULPT_GPENCIL|builtin.select_circle")

        box = layout.box()
        row = box.row()
        row.label(text='PAINT COLOR TOOLS')
        row = box.row(align=True)
        self.addOperator(ctool, row, "quicktools.set_quicktool", "GPBRUSH_PENCIL", "VERTEX_GPENCIL|builtin_brush.Draw")
        row.separator()
        self.addOperator(ctool, row, "quicktools.set_quicktool", "MATFLUID", "VERTEX_GPENCIL|builtin_brush.Blur")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "MOD_SUBSURF", "VERTEX_GPENCIL|builtin_brush.Average")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "OUTLINER_OB_FORCE_FIELD", "VERTEX_GPENCIL|builtin_brush.Smear")
        row.separator()
        self.addOperator(ctool, row, "quicktools.set_quicktool", "GPBRUSH_MARKER", "VERTEX_GPENCIL|builtin_brush.Replace")
        row.separator()
        self.addOperator(ctool, row, "quicktools.set_quicktool", "EXPERIMENTAL", "OPS|FILL")
        
# Class list to register
_classes = [
    SetQuickToolOperator,
    quickToggleFullScreenOperator,
    QuickToolsPanel
]

def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
