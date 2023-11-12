bl_info = {
    "name": "Cut Stroke",
    "author": "pongbuster",
    "version": (1, 0),
    "blender": (2, 90, 0),
    "location": "View3D > Sidebar (N)",
    "description": "Cuts visible strokes on active layer.",
    "warning": "",
    "doc_url": "",
    "category": "Grease Pencil",
}

import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils
from mathutils import Vector
import mathutils

def draw_callback_px(self, context):
    
    if self.first:
        lines = []
        lines.append(self.first)
        lines.append(self.mousepos)
        # 50% alpha, 2 pixel width line
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(2.0)
        batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": lines})
        shader.uniform_float("color", (0.0, 0.0, 0.0, 0.5))
        batch.draw(shader)

        # restore opengl defaults
        gpu.state.line_width_set(1.0)
        gpu.state.blend_set('NONE')


class CutStrokeOperator(bpy.types.Operator):
    """Cut visible strokes on the active layer"""
    bl_idname = "view3d.cutstroke_operator"
    bl_label = "Cut strokes Operator"

    @classmethod
    def poll(self, context):
        return (context.active_object.type == 'GPENCIL')

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
            self.mousepos = (event.mouse_region_x, event.mouse_region_y)

        elif event.type == 'LEFTMOUSE':
            if self.first == None:
                self.first = (event.mouse_region_x, event.mouse_region_y)
                return {'RUNNING_MODAL'}

            self.last = (event.mouse_region_x, event.mouse_region_y)
            
            area = context.area
            space = area.spaces[0]
            
            for region in area.regions:
                if region.type == 'WINDOW':
                    break
                
            pt1 = view3d_utils.region_2d_to_location_3d(context.region, context.space_data.region_3d, 
                (self.first[0], self.first[1]), (0,0,0))
            pt2 = view3d_utils.region_2d_to_location_3d(context.region, context.space_data.region_3d, 
                (self.last[0], self.last[1]), (0,0,0))
                
            lineA_p1 = Vector((pt1[0], pt1[2]))
            lineA_p2 = Vector((pt2[0], pt2[2]))
                
            gp = context.active_object    
            strokes = gp.data.layers.active.active_frame.strokes
            
            for s in strokes:
                cnt = len(s.points)
                for pdx in range(cnt - 1, 0, -1):
                    lineB_p1 = Vector((s.points[pdx - 1].co[0], s.points[pdx - 1].co[2]))
                    lineB_p2 = Vector((s.points[pdx].co[0], s.points[pdx].co[2]))
                    
                    intersect_point = mathutils.geometry.intersect_line_line_2d(lineA_p1, lineA_p2, lineB_p1, lineB_p2)
                    
                    if intersect_point:
                        
                        s.points.add(1)
                    
                        for i in range( len(s.points) - 1, pdx, -1):
                            s.points[i].uv_rotation = s.points[i - 1].uv_rotation
                            s.points[i].uv_fill = s.points[i - 1].uv_fill
                            s.points[i].uv_factor = s.points[i - 1].uv_factor
                            
                            s.points[i].pressure = s.points[i - 1].pressure
                            s.points[i].strength = s.points[i - 1].strength
                            s.points[i].vertex_color = s.points[i - 1].vertex_color
                            
                            s.points[i].co[0] = s.points[i - 1].co[0]
                            s.points[i].co[1] = s.points[i - 1].co[1]
                            s.points[i].co[2] = s.points[i - 1].co[2]
                            s.points[i].select = s.points[i - 1].select
                        

                        s.points[pdx - 0].pressure = s.points[pdx].pressure
                        s.points[pdx - 0].strength = s.points[pdx].strength
                        s.points[pdx - 0].vertex_color = s.points[pdx].vertex_color
                        s.points[pdx - 0].uv_rotation = s.points[pdx].uv_rotation
                        s.points[pdx - 0].uv_fill = s.points[pdx].uv_fill
                        s.points[pdx - 0].uv_factor = s.points[pdx].uv_factor
                        
                        s.points[pdx - 0].co[0] = intersect_point.x
                        s.points[pdx - 0].co[1] = 0
                        s.points[pdx - 0].co[2] = intersect_point.y
                        s.points[pdx].select = True
                                            

            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D' and context.active_object.type == 'GPENCIL':
            # the arguments we pass the the callback
            args = (self, context)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

            self.first = None
            self.mousepos = None

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(CutStrokeOperator)


def unregister():
    bpy.utils.unregister_class(CutStrokeOperator)


if __name__ == "__main__":
    register()
