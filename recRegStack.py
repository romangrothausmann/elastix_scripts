## https://github.com/kaspermarstal/SimpleElastix/blob/master/Examples/Python/SimpleElastix.py

import SimpleITK as sitk
import sys
import os
import glob
import re

### BEGIN https://stackoverflow.com/questions/4675728/redirect-stdout-to-a-file-in-python#22434262

from contextlib import contextmanager

def fileno(file_or_fd):
    fd = getattr(file_or_fd, 'fileno', lambda: file_or_fd)()
    if not isinstance(fd, int):
        raise ValueError("Expected a file (`.fileno()`) or a file descriptor")
    return fd

@contextmanager
def stdout_redirected(to=os.devnull, stdout=None):
    if stdout is None:
       stdout = sys.stdout

    stdout_fd = fileno(stdout)
    # copy stdout_fd before it is overwritten
    #NOTE: `copied` is inheritable on Windows when duplicating a standard stream
    with os.fdopen(os.dup(stdout_fd), 'wb') as copied: 
        stdout.flush()  # flush library buffers that dup2 knows nothing about
        try:
            os.dup2(fileno(to), stdout_fd)  # $ exec >&to
        except ValueError:  # filename
            with open(to, 'wb') as to_file:
                os.dup2(to_file.fileno(), stdout_fd)  # $ exec > to
        try:
            yield stdout # allow code to be run with the redirected stdout
        finally:
            # restore stdout to its previous value
            #NOTE: dup2 makes stdout_fd inheritable unconditionally
            stdout.flush()
            os.dup2(copied.fileno(), stdout_fd)  # $ exec >&copied

### END https://stackoverflow.com/questions/4675728/redirect-stdout-to-a-file-in-python#22434262


# Instantiate SimpleElastix
selx = sitk.ElastixImageFilter() # https://github.com/SuperElastix/SimpleElastix/issues/99#issuecomment-308132783
stfx = sitk.TransformixImageFilter()
selx.LogToFileOff()
selx.LogToConsoleOn()
stfx.LogToFileOff()
stfx.LogToConsoleOff() # no effect if selx.LogToConsoleOn() ?

selx.SetParameterMap(selx.ReadParameterFile(str(sys.argv[3]))) # https://github.com/kaspermarstal/SimpleElastix/blob/master/Code/Elastix/include/sitkSimpleElastix.h#L119
# selx.PrintParameterMap()

FNs= sorted( glob.glob(sys.argv[1]) ) # http://stackoverflow.com/questions/6773584/how-is-pythons-glob-glob-ordered # http://stackoverflow.com/questions/3207219/how-to-list-all-files-of-a-directory-in-python#3215392
FNo= sys.argv[2] # FNo= os.path.abspath(FNs[0]) + "/reg/"
if not os.path.exists(FNo): # http://stackoverflow.com/questions/273192/how-to-check-if-a-directory-exists-and-create-it-if-necessary
    os.makedirs(FNo)

## copy first file as is or transform with identity

for idx, FN in enumerate(FNs):
    FN0= FNs[(idx - 1) % len(FNs)] # http://stackoverflow.com/questions/2167868/getting-next-element-while-cycling-through-a-list#2167962
    FN1= FN
    FNof= sys.argv[2] + "/" + os.path.splitext(FN1)[0] + ".tif" # TIF for float # http://stackoverflow.com/questions/678236/how-to-get-the-filename-without-the-extension-from-a-path-in-python
    FNt= sys.argv[2] + "/" + os.path.splitext(FN1)[0] + ".txt"
    DNl= sys.argv[2] + "/" + os.path.splitext(FN1)[0] + ".log/"

    
    if not os.path.exists(DNl):
        os.makedirs(DNl)
    selx.SetOutputDirectory(DNl)

    elastixLog= os.path.splitext(FN1)[0] + ".log"
    selx.SetLogFileName(elastixLog)
    elastixLogPath= DNl + elastixLog

    print("\r%5.1f%% (%d/%d)" % ((idx+1) * 100.0 / len(FNs), idx+1, len(FNs))),
    sys.stdout.flush() # essential with \r !
    
    mI= sitk.ReadImage(FN1)
    PixelType= mI.GetPixelIDValue()
        
    if idx == 0:
        sitk.WriteImage(sitk.Cast(mI, PixelType), FNof)
        continue

    fI= sitk.ReadImage(FN0)

    selx.SetFixedImage(fI) # https://github.com/kaspermarstal/SimpleElastix/blob/master/Code/IO/include/sitkImageFileReader.h#L73
    selx.SetMovingImage(mI)
    with open(elastixLogPath, 'w') as f, stdout_redirected(f):
        selx.Execute()
    f.close()

    finalMetricValue= 0
    with open(elastixLogPath) as f:
        m= re.search('Final metric value  = (?P<value>[+-.0-9]{9})', f.read()) # http://lists.bigr.nl/pipermail/elastix/2016-December/002435.html
    f.close()
    if m:
        try:
            finalMetricValue= float(m.group('value'))
        except:
            raise Exception('Final metric value not found in "elastix.log".')
    print(finalMetricValue)

    tM= selx.GetTransformParameterMap(0)
    if idx > 1:
        tM['InitialTransformParametersFileName'] = [ str(os.path.splitext( sys.argv[2] + "/" + FNs[(idx - 1) % len(FNs)] )[0] + ".txt") ]

    stfx.AddTransformParameterMap(tM)
    stfx.SetMovingImage(mI)
    with stdout_redirected(): # siclence stfx.Execute()
        stfx.Execute()

    # Write result image
    sitk.WriteImage(sitk.Cast(stfx.GetResultImage(), PixelType), FNof)
    selx.WriteParameterFile(selx.GetTransformParameterMap(0), FNt)

