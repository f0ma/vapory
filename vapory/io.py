"""
All the advanced Input/Output operations for Vapory
"""

import re
import os
import subprocess
import tempfile
from .config import POVRAY_BINARY

try:
    import numpy
    numpy_found=True
except IOError:
    numpy_found=False

try:
    from IPython.display import Image
    ipython_found=True
except:
    ipython_found=False

def ppm_to_numpy(filename=None, buffer=None, byteorder='>'):
    """Return image data from a raw PGM/PPM file as numpy array.

    Format specification: http://netpbm.sourceforge.net/doc/pgm.html

    """

    if not numpy_found:
        raise IOError("Function ppm_to_numpy requires numpy installed.")

    if buffer is None:
        with open(filename, 'rb') as f:
            buffer = f.read()
    try:
        header, width, height, maxval = re.search(
            b"(^P\d\s(?:\s*#.*[\r\n])*"
            b"(\d+)\s(?:\s*#.*[\r\n])*"
            b"(\d+)\s(?:\s*#.*[\r\n])*"
            b"(\d+)\s(?:\s*#.*[\r\n]\s)*)", buffer).groups()
    except AttributeError:
        raise ValueError("Not a raw PPM/PGM file: '%s'" % filename)

    cols_per_pixels = 1 if header.startswith(b"P5") else 3

    dtype = 'uint8' if int(maxval) < 256 else byteorder+'uint16'
    arr = numpy.frombuffer(buffer, dtype=dtype,
                           count=int(width)*int(height)*3,
                           offset=len(header))

    return arr.reshape((int(height), int(width), 3))



def render_povstring(string, **kwargs):

    """ Renders the provided scene description with POV-Ray.

    Parameters
    ------------

    string
      A string representing valid POVRay code. Typically, it will be the result
      of scene(*objects)

    outfile
      Name of the PNG file for the output.
      If outfile is None, a numpy array is returned (if numpy is installed).
      If outfile is 'ipython' and this function is called last in an IPython
      notebook cell, this will print the result in the notebook.

    height
      height in pixels

    width
      width in pixels
      
    tempfile
      temprorary .pov file name, default '__temp__.pov'
    
    preserve_temp
      save .pov file after rendering, default False
      
    quality
      quality value in [0..9], default None
    
    antialiasing
      antialiasing level in [0..9], default None
      
    antialias_depth
      antialias_depth in [0.0..1.0], default None
    
    jitter
      enable jitter, default False
      
    show_window
      show povray window, default False
      
    output_alpha
      enable alpha in output, default False    
    
    include_dirs
      include directory, default []
    
    """

    pov_file = kwargs['tempfile'] if 'tempfile' in kwargs else ''
    
    if pov_file == '':
        f, pov_file = tempfile.mkstemp(suffix='.pov')
        os.write(f, string.encode('ascii'))
        os.close(f)
    else:
        with open(pov_file, 'w+') as f:
            f.write(string)

    return_np_array = 'outfile' not in kwargs
    
    display_in_ipython = 'outfile' in kwargs and kwargs['outfile']=='ipython'

    format_type = "P" if return_np_array else "N"

    outfile_name = kwargs['outfile'] if 'outfile' in kwargs else ""

    if return_np_array:
        outfile_name='-'

    if display_in_ipython:
        outfile_name = '__temp_ipython__.png'

    cmd = [POVRAY_BINARY, pov_file]
    
    if 'height' in kwargs: cmd.append('+H%d'%kwargs['height'])
    if 'width'  in kwargs: cmd.append('+W%d'%kwargs['width'])
    if 'quality' in kwargs: cmd.append('+Q%d'%kwargs['quality'])
    if 'antialiasing' in kwargs: cmd.append('+A%f'%kwargs['antialiasing'])
    if 'antialias_depth'  in kwargs: cmd.append('+R%f'%kwargs['antialias_depth'])
    if 'jitter' in kwargs and kwargs['jitter']: cmd.append('+J')
    
    if 'show_window' in kwargs and kwargs['show_window']:
        cmd.append('+D')
    else:
        cmd.append('-D')
    
    if 'output_alpha' in kwargs and kwargs['output_alpha']:
        cmd.append("+UA")
    
    if 'include_dirs' in kwargs and kwargs['include_dirs'] != []:
        for dir in kwargs['include_dirs']:
            cmd.append('+L%s'%dir)
    
    cmd.append("Output_File_Type=%s"%format_type)
    cmd.append("+O%s"%outfile_name)
    
    process = subprocess.Popen(cmd, stderr=subprocess.PIPE,
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE)

    out, err = process.communicate()

    if 'preserve_temp' in kwargs and kwargs['preserve_temp']:
        pass
    else:
        os.remove(pov_file)

    if process.returncode:
        print(err.decode('ascii'))
        raise IOError("POVRay rendering failed with error")

    if return_np_array:
        return ppm_to_numpy(buffer=out)

    if display_in_ipython:
        if not ipython_found:
            raise("The 'ipython' option only works in the IPython Notebook.")
        return Image(outfile)
