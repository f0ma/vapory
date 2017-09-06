from copy import deepcopy
import math
from .helpers import format_if_necessary
from .io import render_povstring
from threading import Thread
import time
import threading

try:
    import queue
except:
    import Queue as queue


class Vector(object):
    def __init__(self,*args):
        if len(args) == 0:
            raise ValueError("Can't create empty vector")
        if len(args) == 1 and (type(args[0]) == list or type(args[0]) == tuple):
            self.vector = list(arg[0])
        else:
            self.vector = list(args)

    def copy(self):
        return deepcopy(self)            

    def __str__(self):
        return "< %s >" % (", ".join([str(format_if_necessary(e)) for e in self.vector]))


class Value(object):
    def __init__(self, value):
        self.value = value

    def copy(self):
        return deepcopy(self)            

    def __str__(self):
        return "%s" % str(format_if_necessary(self.value))

class Episode:
    def __init__(self, length):
        self.length = length
        self.actionline = []
        
    def change_vector(self, vec, arg1, arg2 = None, dynamic = 'linear', scale = 1.0):

        if type(vec) != Vector:
            raise ValueError('Vector class object requried')
        
        if arg2 == None:
            x_from = vec.copy()
            x_to = arg1
        else:
            x_from = arg1
            x_to = arg2
        
        self.actionline.append({'process': 'change_vector_'+dynamic,
                                'obj':vec,
                                's':x_from,
                                'p':x_to,
                                'scale':scale})

    def change_value(self, val, arg1, arg2 = None, dynamic = 'linear', scale = 1.0):
        
        if type(val) != Value:
            raise ValueError('Vector class object requried')
        
        if arg2 == None:
            x_from = val.copy()
            x_to = arg1
        else:
            x_from = arg1
            x_to = arg2

        self.actionline.append({'process': 'change_value_'+dynamic,
                                'obj':val, 
                                's':x_from,
                                'p':x_to,
                                'scale':scale})
       
    def operate(self, t_point):
        for a in self.actionline:
            if a['process'] == 'change_value_linear':
                r_val = a['s'].value+(a['p'].value-a['s'].value)*t_point*a['scale']
                a['obj'].value = r_val
            if a['process'] == 'change_value_tanhyp':
                r_val = a['s'].value+(a['p'].value-a['s'].value)*math.tanh(t_point*3)*a['scale']
                a['obj'].value = r_val
            if a['process'] == 'change_vector_linear':
                r_vec = [s+((p-s)*t_point)*a['scale'] for s,p in zip(a['s'].vector,a['p'].vector)]
                a['obj'].vector = r_vec
            if a['process'] == 'change_vector_tanhyp':
                r_vec = [s+((p-s)*math.tanh(t_point*3))*a['scale'] for s,p in zip(a['s'].vector,a['p'].vector)]
                a['obj'].vector = r_vec



class RenderThread(Thread):
    def __init__(self, suite):
        Thread.__init__(self)
        self.suite = suite
        self.working = True
    def run(self):
        while self.working:
            try:
                task = self.suite.tasks_queue.get_nowait()
                render_povstring(task[0], **task[1])        
                self.suite.tasks_queue.task_done()
            except queue.Empty:
                time.sleep(1)
            
class Suite:
    def __init__(self):
        self.episodes = []
        self.render_args = {'fps':25}
        self.current_card = None
        self.thread_pool = None
        self.thread_pool_count = 0
        self.tasks_queue = None
        self.status_template = "episode: [{}/{}], frame [{}/{}]"
        self.status_string = ""
        pass
    
    def setup_pool(self, thread_count=2, queue_size=5):
        self.thread_pool_count = thread_count
        self.thread_pool = []
        self.tasks_queue = queue.Queue(queue_size)
        for _ in range(0, thread_count):
            self.thread_pool.append(RenderThread(self))
            self.thread_pool[-1].start()

    
    def make_episode(self, length):
        ep = Episode(length)
        self.episodes.append(ep)
        return ep
    
    def play(self):
        for i,ep in enumerate(self.episodes):
            el_len_count = ep.length * self.render_args['fps']
            for el_pos_num in range(0, el_len_count+1):
                self.status_string = self.status_template.format(i,len(self.episodes),el_pos_num,el_len_count+1)
                el_t_pos = float(el_pos_num)/float(el_len_count)
                ep.operate(el_t_pos)
                self.current_card = str(i).zfill(6)+str(el_pos_num).zfill(6)
                yield self.current_card

    def setup(self, **kwargs):
        self.render_args.update(kwargs)
    
    def prepare_render_args(self, **kwargs):
        current_render_args = deepcopy(self.render_args)
        current_render_args.update(kwargs)
        if 'outfile' not in current_render_args:
            current_render_args['outfile'] = self.current_card+".png"
        
        if 'outdir' in current_render_args:
            current_render_args['outfile'] = current_render_args['outdir'] +'/'+ current_render_args['outfile']
        return current_render_args
    
    def render(self, scene, **kwargs):
        wargs = self.prepare_render_args(**kwargs)
        scene.render(**wargs)
    
    def render_in_pool(self, scene, **kwargs):
        if self.tasks_queue == None:
            raise ValueError("Thread pool not ready. Run setup_pool first")
        scene_code = str(scene)
        kkwargs = self.prepare_render_args(**kwargs)
        self.tasks_queue.put((scene_code, kkwargs))
    
    def join_pool(self):
        for t in self.thread_pool:
            t.working = False
            t.join()
