from vapory import *
import os

sphere_center = Vector(0,20,2)

camera = Camera( 'location', Vector(0,5,20), 'look_at', Vector(0,0,0) )
light = LightSource( Vector(-30,10,20), 'color', Vector(1,1,1) )
sphere = Sphere( sphere_center, Value(2), Texture( Pigment( 'color', Vector(1,0,1) )))

textr = Texture( Pigment( 'color', Vector(1,0,1) ))

tr1 = Torus(4,0.12, textr, 'translate', Vector(0,-5,0))
tr2 = Torus(4,0.12, textr, 'translate', Vector(0,5,0))

qtc = Cylinder(Vector(0,-30,0), Vector(0,30,0), Value(0.12), textr)


c1 = Cylinder(Vector(0,-5,4), Vector(0,5,4), Value(0.12), textr)
c2 = Cylinder(Vector(0,-5,-4), Vector(0,5,-4), Value(0.12), textr)

r1 =  Sphere(Vector(0,-5,4),Value(0.3), textr)
r2 =  Sphere(Vector(0,-5,-4),Value(0.3), textr)
r3 =  Sphere(Vector(0,5,-4),Value(0.3), textr)
r4 =  Sphere(Vector(0,5,4),Value(0.3), textr)

rotcylvec = Vector(0,60,0)

ov = Union(tr1, tr2, c1,c2,r1,r2,r3,r4, 'rotate', rotcylvec)

rcnt = Sphere(Vector(0,0,0),Value(1), Texture( Pigment( 'color', Vector(1,0,0) )))

rotvec = Vector(10,60,0)

od = Union(ov,rcnt,qtc,'rotate',rotvec)

suite = Suite()

ep_show = suite.make_episode(15)

ep_show.change_vector(rotvec , Vector(10,60+360,0))

ep_show.change_vector(rotcylvec , Vector(0,60+360,0))

if not os.path.exists('imgs'):
    os.makedirs('imgs')

suite.setup(outdir="imgs",
            fps=25,
            width=160,
            height=120,
            antialiasing = 0.2)


suite.setup_pool(4)

for cadr in suite.play():
    suite.render_in_pool(Scene( camera, objects= [light, sphere, od]))

suite.join_pool()
