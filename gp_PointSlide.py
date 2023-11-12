bl_info = {
    "name": "Point Slide",
    "author": "pongbuster",
    "version": (1, 0),
    "blender": (2, 90, 0),
    "location": "View3D > Sidebar (N)",
    "description": "Slides selected points along their normals.",
    "warning": "",
    "doc_url": "",
    "category": "Grease Pencil",
}

import bpy
import blf
import gpu
from mathutils import Vector
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils

from bpy.props import IntProperty, FloatProperty

selected_points = []

def init_selected(context):
    gp = bpy.context.active_object
    
    selected_points.clear()

    stroke_start = 0
    
    strokes = gp.data.layers.active.active_frame.strokes
    
    for sdx,s in enumerate(strokes):
        if sdx > 0: 
            stroke_start = len(selected_points)
            selected_points.append(None)
        for pdx,p in enumerate(s.points):
            if p.select:
                v1 = Vector((p.co[0], p.co[1], p.co[2]))
                pdx0 = pdx - 1
                pdx2 = pdx + 1
                if pdx0 < 0:
                    if s.use_cyclic == False:
                        pdx0 = None
                    else:
                        pdx0 += len(s.points)
                if pdx2 > len(s.points) - 1:
                    if s.use_cyclic == False:
                        pdx2 = None
                    else:
                        pdx2 -= len(s.points)
                
                if pdx0 == None or pdx2 == None:
                    vn = Vector((0, 0, 0))
                else:
                    v0 = Vector((s.points[pdx0].co[0], s.points[pdx0].co[1], s.points[pdx0].co[2]))
                    v2 = Vector((s.points[pdx2].co[0], s.points[pdx2].co[1], s.points[pdx2].co[2]))
                    vn = ((v0 - v1) + (v2 - v1)) / 2
                    
                    vn1 = v1 - v0
                    vn1 = Vector((vn1.z, vn1.y, -vn1.x))
                    vn1.normalize()
                    vn2 = v2 - v1
                    vn2 = Vector((vn2.z, vn2.y, -vn2.x))
                    vn2.normalize()
                    vn = (vn1 + vn2) / 2
                    vn.normalize()
                selected_points.append( (sdx, pdx, v1, vn) )
        if s.select and s.use_cyclic:
            if s.points[0].select and s.points[len(s.points) - 1].select:
                selected_points.append( selected_points[stroke_start] )
            
                            

def draw_callback_px(self, context):
    font_id = 0  # XXX, need to find out how best to get this.

    # draw some text
    blf.position(font_id, 15, 30, 0)
    blf.size(font_id, 20, 72)
    #blf.draw(font_id, "Hello Word: " + str(self.delta))

    # 50% alpha, 2 pixel width line
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    shader.uniform_float("color", (0.0, 0.0, 0.0, 0.5))

    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(2.0)

    area = context.area
    space = area.spaces[0]
    
    for region in area.regions:
        if region.type == 'WINDOW':
            break
        
    lines = []
    for sp in selected_points:
        if sp == None:
            batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": lines})
            batch.draw(shader)
            lines.clear()
            continue
        lines.append(view3d_utils.location_3d_to_region_2d(region, space.region_3d, sp[2] + sp[3] * self.delta))
    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": lines})
    batch.draw(shader)

    # restore opengl defaults
    gpu.state.line_width_set(1.0)
    gpu.state.blend_set('NONE')

class PointSlideOperator(bpy.types.Operator):
    """Slide selected points along point normals."""
    bl_idname = "object.pointslide_operator"
    bl_label = "Point Slide Operator"

    first_mouse_x: IntProperty()
    first_value: FloatProperty()

    @classmethod
    def poll(self, context):
        return (context.active_object.type == 'GPENCIL')

    def modal(self, context, event):
        context.area.tag_redraw()
        if event.type == 'MOUSEMOVE':
            context.area.tag_redraw()
            self.delta = (self.first_mouse_x - event.mouse_x) * 0.001

        elif event.type == 'LEFTMOUSE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            context.area.tag_redraw()
            
            gp = context.active_object
            strokes = gp.data.layers.active.active_frame.strokes
            for sp in selected_points:
                if sp is not None:
                    v = sp[2] + sp[3] * self.delta
                    stroke = strokes[sp[0]]
                    point = stroke.points[sp[1]]
                    point.co[0] = v.x
                    point.co[1] = v.y
                    point.co[2] = v.z
                
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            context.area.tag_redraw()
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.object.type == 'GPENCIL':
            
            init_selected(context)
            self.first_mouse_x = event.mouse_x
            self.delta = 0.0

            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "No active object, could not finish")
            return {'CANCELLED'}


class PointSlidePanel(bpy.types.Panel):
    bl_label = "Point Slide Panel"
    bl_idname = "OBJECT_PT_PointSlidePanel"
    
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Grease Pencil"
    
    def draw(self, context):
        row = self.layout.row()
        row.operator( 'object.pointslide_operator' )
        
# Class list to register
_classes = [
    PointSlideOperator,
#    PointSlidePanel,
]

def register():
    for cls in _classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

    # test call
#    bpy.ops.object.pointslide_operator('INVOKE_DEFAULT')
