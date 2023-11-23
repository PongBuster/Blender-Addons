bl_info = {
    "name": "GPencil QuickTools",
    "author": "pongbuster",
    "version": (1, 6),
    "blender": (2, 80, 0),
    "location": "View3D > N sidebar",
    "description": "Adds grease pencil tool shortcuts to N sidebar",
    "warning": "",
    "doc_url": "",
    "category": "Grease Pencil",
}

import bpy
import gpu
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

def cmp(clr1, clr2):
    delta = 0.03
    return abs(clr1[0] - clr2[0]) < delta and abs(clr1[1] - clr2[1]) < delta and abs(clr1[2] - clr2[2]) < delta

def getPixel(X, Y):
    fb = gpu.state.active_framebuffer_get()
    screen_buffer = fb.read_color(X, Y, 1, 1, 3, 0, 'FLOAT')

    rgb_as_list = screen_buffer.to_list()[0]

    R = rgb_as_list[0][0]
    G = rgb_as_list[0][1]
    B = rgb_as_list[0][2]

    return R, G, B
    
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
    
    def frameSelection(self, context):
        gp = context.active_object

        if gp.type != 'GPENCIL':
            return
        
        minx = miny = 9999
        maxx = maxy = -9999
        avg = Vector((0,0,0))
        
        for lr in gp.data.layers:
            if lr.lock == True or lr.hide == True or not lr.active_frame:
                continue
            for s in lr.active_frame.strokes:            
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
        

    def createMaterialsFromStrokes(self, context):
        gp = context.active_object
        
        for layer in gp.data.layers:
            for frame in layer.frames:
                for stroke in frame.strokes:
                    if len(stroke.points) == 0 : continue
                
                    mat_index = stroke.material_index
                    vertex_color = vertex_color_fill = None
                    if gp.data.materials[mat_index].grease_pencil.show_fill:
                        vertex_color_fill = stroke.vertex_color_fill
                    if gp.data.materials[mat_index].grease_pencil.show_stroke:
                        vertex_color = stroke.points[0].vertex_color     

                    # skip strokes drawn with material color
                    if (vertex_color_fill and stroke.vertex_color_fill[3] == 0) and \
                        (vertex_color and stroke.points[0].vertex_color[3] == 0):
                        continue

                    bFound = False
                    
                    for idx in range(0, len(gp.data.materials)):
                        mat = gp.data.materials[idx].grease_pencil
                        
                        mc = [ mat.color[0], mat.color[1], mat.color[2] ]
                        mf = [ mat.fill_color[0], mat.fill_color[1], mat.fill_color[2] ]

                        if vertex_color and not vertex_color_fill:
                            sc = [ vertex_color[0], vertex_color[1], vertex_color[2] ]
                            if mat.show_stroke and not mat.show_fill and cmp(sc, mc):
                                stroke.material_index = idx
                                bFound = True
                                break
                                
                        if vertex_color_fill and not vertex_color:
                            sf = [ vertex_color_fill[0], vertex_color_fill[1], vertex_color_fill[2]]
                            if mat.show_fill and not mat.show_stroke and cmp(sf, mf):
                                stroke.material_index = idx
                                bFound = True
                                break
                            
                        if vertex_color and vertex_color_fill:
                            sc = [ vertex_color[0], vertex_color[1], vertex_color[2] ]
                            sf = [ vertex_color_fill[0], vertex_color_fill[1], vertex_color_fill[2]]
                            if mat.show_stroke and mat.show_fill and cmp(sc, mc) and cmp(sf, mf):
                                stroke.material_index = idx
                                bFound = True
                                break
                                    
                    if bFound == False:
                        # create new material    
                        gp_mat = bpy.data.materials.new("COLOR" + str( len(gp.data.materials) + 1) )

                        if not gp_mat.is_grease_pencil:
                            bpy.data.materials.create_gpencil_data(gp_mat)
                            if vertex_color:
                                gp_mat.grease_pencil.color = (vertex_color[0], vertex_color[1], vertex_color[2], 1)
                                gp_mat.grease_pencil.show_stroke=True
                            else:
                                gp_mat.grease_pencil.show_stroke=False
                            
                            if vertex_color_fill:
                                gp_mat.grease_pencil.fill_color = (vertex_color_fill[0], vertex_color_fill[1], vertex_color_fill[2], 1) 
                                gp_mat.grease_pencil.show_fill=True
                            else:
                                gp_mat.grease_pencil.show_fill=False

                        gp.data.materials.append(gp_mat)
                        stroke.material_index = len(gp.data.materials) - 1
                        stroke.vertex_color_fill[3] = 0
                        stroke.points[0].vertex_color[3] ==0
                        
                                
    def execute(self, context):
        
        mode, cmd = self.args.split('|')

        if mode == 'OPS':
            
            if cmd == 'OBJECTMODE':
                bpy.ops.object.mode_set(mode='OBJECT')
            elif cmd == 'UNDO':
                try: bpy.ops.ed.undo()
                except: None
            elif cmd == 'REDO':
                try: bpy.ops.ed.redo()
                except: None
            elif cmd == 'FULLSCREEN':
                bpy.ops.quicktools.togglefullscreen()
            elif cmd == 'BOUNDS':
                bpy.ops.view3d.view_center_camera()
            elif cmd == 'SCULPT_POINT':
                 bpy.context.scene.tool_settings.use_gpencil_select_mask_point = not bpy.context.scene.tool_settings.use_gpencil_select_mask_point
            elif cmd == 'SCULPT_STROKE':
                 bpy.context.scene.tool_settings.use_gpencil_select_mask_stroke = not bpy.context.scene.tool_settings.use_gpencil_select_mask_stroke
            elif cmd == 'FRAME':
                self.frameSelection(context)
            elif cmd == 'CREATE_MATERIALS':
                self.createMaterialsFromStrokes(context)
            elif cmd == 'LAYER':
                gp = context.active_object
                for idx, lr in enumerate(gp.data.layers):
                    for s in lr.active_frame.strokes:
                        if s.select:
                            gp.data.layers.active_index = idx
                            break
            elif cmd == 'FILL':
                gp = context.active_object
                clr = bpy.data.brushes['Vertex Replace'].color
                
                for lr in gp.data.layers:
                    for s in lr.active_frame.strokes:
                        for p in s.points:
                            if p.select:
                                 s.vertex_color_fill = (s2lin(clr[0]), s2lin(clr[1]), s2lin(clr[2]), 1)
                                 
            else: # change to edit mode to run stroke commands, return to previous mode after
                _mode = context.active_object.mode
                bpy.ops.object.mode_set(mode='EDIT_GPENCIL')

                if cmd == 'JOIN':
                    bpy.ops.gpencil.stroke_join(type='JOIN')
                elif cmd == 'CLOSE':
                    bpy.ops.gpencil.stroke_cyclical_set(type='CLOSE', geometry=True)
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
                elif cmd == 'LINKED':
                    bpy.ops.gpencil.select_linked()
                elif cmd == 'BRING_TO_FRONT':
                    bpy.ops.gpencil.stroke_arrange(direction='TOP')
                elif cmd == 'BRING_FORWARD':
                    bpy.ops.gpencil.stroke_arrange(direction='UP')
                elif cmd == 'SEND_BACKWARD':
                    bpy.ops.gpencil.stroke_arrange(direction='DOWN')
                elif cmd == 'SEND_TO_BACK':
                    bpy.ops.gpencil.stroke_arrange(direction='BOTTOM')
                else:
                    print(cmd + " not handled")
                    
                bpy.ops.object.mode_set(mode=_mode)
                
        else:
            try:
                bpy.context.object.data.use_curve_edit = False
                bpy.ops.object.mode_set(mode=self.args.split('|')[0])
                bpy.ops.wm.tool_set_by_id(name=self.args.split('|')[1])
            except:
                print("Exception raised with:" + self.args)

        return {'FINISHED'}


class quickEyeDropperOperator(bpy.types.Operator):
    """Left click to sample Fill color.
SHIFT-Left click to sample Stroke color.
"""

    bl_idname = "quicktools.eyedropper"
    bl_label = "QuickTools Color Eyedropper"
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


class quickSampleStrokesOperator(bpy.types.Operator):
    """
    Sample selected stroke with new points. Scroll mouse wheel to add / remove number of points.
    Hold shift for higher detail. Left click to apply. Right click to cancel.
    """
    
    bl_idname = "quicktools.sample_strokes"
    bl_label = "Sample Stroke"
    bl_options = {'REGISTER', 'UNDO'}

    _sample_interval = 0.01
    _sample_length = 0.04
    
    @classmethod
    def poll(self, context):
        return (context.mode == 'SCULPT_GPENCIL' or context.mode == 'EDIT_GPENCIL')
    
    def modal(self, context, event):
        if event.shift:
            self.sample_interval = 0.001
        else:
            self.sample_interval = 0.01

        if event.type == 'WHEELUPMOUSE':
            if self._sample_length - self.sample_interval > 0:
                self._sample_length -= self.sample_interval
            context.area.header_text_set("Sample Length: %.4f" % self._sample_length)
            bpy.ops.gpencil.stroke_sample(length=self._sample_length)

        elif event.type == 'WHEELDOWNMOUSE':
            self._sample_length += self.sample_interval
            context.area.header_text_set("Sample Length: %.4f" % self._sample_length)
            bpy.ops.gpencil.stroke_sample(length=self._sample_length)

        elif event.type == "LEFTMOUSE":
            context.scene['sample_length'] = self._sample_length
            context.area.header_text_set(None)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            context.area.header_text_set(None)
            bpy.ops.ed.undo()
            return {'CANCELLED'}
       
        return {'RUNNING_MODAL'}    
    
    def execute(self, context):
        self._sample_length = context.scene.get('sample_length')
        if not self._sample_length: self._sample_length = 0.04
        
        context.area.header_text_set("Sample Length: %.4f" % self._sample_length)
        context.scene.tool_settings.gpencil_selectmode_edit = 'POINT'    
        context.tool_settings.use_gpencil_select_mask_stroke=False
        context.tool_settings.use_gpencil_select_mask_point=True

        bpy.ops.gpencil.stroke_sample(length=self._sample_length)
        
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}
    
    
class quickToggleFullScreenOperator(bpy.types.Operator):
    bl_idname = "quicktools.togglefullscreen"    
    bl_label = "Quick Toggle FullScreen"
    
    _timer = None
    _original_area = None

    def show(self, context, isFull):
        if context.area:
            isFullScreen = context.window.width == context.area.width
        else:
            isFullScreen = True
            
        if not isFullScreen:
           context.window.cursor_modal_set("NONE")
        else:
           context.window.cursor_modal_restore()
        
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
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':        
                _original_area = context.area
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
        
        row = layout.box().row()
        row.operator("quicktools.set_quicktool", text = "Create Materials").args = "OPS|CREATE_MATERIALS"
        row.operator('quicktools.eyedropper', icon = 'EYEDROPPER', text = "")
        
        box = layout.box()
        row = box.row()
        row.label(text='EDIT TOOLS')
        
        row = box.row(align=True)
        self.addOperator(ctool, row, "quicktools.set_quicktool", "RESTRICT_SELECT_OFF", "EDIT_GPENCIL|builtin.select_box")
        row.separator()
        row.operator("quicktools.set_quicktool", icon = "PARTICLE_DATA").args = "OPS|LINKED"
        row.separator()

        selectmode = bpy.context.scene.tool_settings.gpencil_selectmode_edit
        row.operator("quicktools.set_quicktool", icon="GP_SELECT_POINTS", depress=selectmode=="POINT").args = "OPS|EDIT_POINT"
        row.operator("quicktools.set_quicktool", icon="GP_SELECT_STROKES", depress=selectmode=="STROKE").args = "OPS|EDIT_STROKE"
        row.separator()
        row.operator("quicktools.sample_strokes", icon="PARTICLE_POINT", text ="")
        row.separator()
        row.operator("quicktools.set_quicktool", icon="VIEW_ORTHO").args = "OPS|SUBDIVIDE"

        row = box.row(align=True)
         
        self.addOperator(ctool, row, "quicktools.set_quicktool", "ARROW_LEFTRIGHT", "EDIT_GPENCIL|builtin.move")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "FILE_REFRESH", "EDIT_GPENCIL|builtin.rotate")
        self.addOperator(ctool, row, "quicktools.set_quicktool", "MOD_LENGTH", "EDIT_GPENCIL|builtin.scale")
        row.separator()

        row.operator("quicktools.set_quicktool", icon="RENDERLAYERS").args = "OPS|LAYER"

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
    quickEyeDropperOperator,
    quickSampleStrokesOperator,
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
