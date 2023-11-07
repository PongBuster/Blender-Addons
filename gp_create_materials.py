import bpy

context = bpy.context

gp = context.active_object
if gp == None or gp.type != 'GPENCIL':
    exit

NUM_COLOR_ATTRIB_MATERIALS = len(gp.data.materials)

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
            
            bFound = False
            
            for idx in range(NUM_COLOR_ATTRIB_MATERIALS, len(gp.data.materials)):
                mat = gp.data.materials[idx].grease_pencil
                
                mc = [ mat.color[0], mat.color[1], mat.color[2] ]
                mf = [ mat.fill_color[0], mat.fill_color[1], mat.fill_color[2] ]

                if vertex_color and not vertex_color_fill:
                    sc = [ vertex_color[0], vertex_color[1], vertex_color[2] ]
                    if mat.show_stroke and not mat.show_fill and sc == mc:
                        stroke.material_index = idx
                        bFound = True
                        break
                        
                if vertex_color_fill and not vertex_color:
                    sf = [ vertex_color_fill[0], vertex_color_fill[1], vertex_color_fill[2]]
                    if mat.show_fill and not mat.show_stroke and sf == mf:
                        stroke.material_index = idx
                        bFound = True
                        break
                    
                if vertex_color and vertex_color_fill:
                    sc = [ vertex_color[0], vertex_color[1], vertex_color[2] ]
                    sf = [ vertex_color_fill[0], vertex_color_fill[1], vertex_color_fill[2]]
                    if mat.show_stroke and mat.show_fill and sc == mc and sf == mf:
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