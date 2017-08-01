## https://github.com/kaspermarstal/SimpleElastix/blob/master/Examples/Python/SimpleElastix.py

import SimpleITK as sitk
import sys
import argparse
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


def main():
    
    usage_text =  "Run SimpleElastix sequentially on series images:"
    usage_text +=  __file__ + " [options]"
    
    parser = argparse.ArgumentParser(description=usage_text)

    parser.add_argument("-i", "--inputPattern", dest="input", metavar='GlobPattern', required=True, help="Glob-pattern for input files.")
    parser.add_argument("-o", "--output", dest="output", metavar='DestDir', required=True, help="Output dir to save the result images in.")
    parser.add_argument("-p", "--paramFile", dest="PF", metavar='ParamFile', required=True, help="Elastix Parameter File")
    parser.add_argument("-s", "--start", dest="start", required=False, help="Skip images before specified start-file.")
    parser.add_argument("-S", "--skip", dest="skip", metavar='N', nargs='+', help="Skip specified file-names.")


    args = parser.parse_args()

    FNs= sorted( glob.glob(args.input) ) # http://stackoverflow.com/questions/6773584/how-is-pythons-glob-glob-ordered # http://stackoverflow.com/questions/3207219/how-to-list-all-files-of-a-directory-in-python#3215392
    FNs= [x for x in FNs if x not in args.skip] # removing by index (less suitable): [FNs.pop(x) for x in args.skip]
    try:
        start= FNs.index(args.start) # can be used as FNs= FNs[start:] but not ideal for referencing idx-1
    except ValueError, e:
        start= None
        print "Start not found!"
    
    FNo= args.output # FNo= os.path.abspath(FNs[0]) + "/reg/"
    if not os.path.exists(FNo): # http://stackoverflow.com/questions/273192/how-to-check-if-a-directory-exists-and-create-it-if-necessary
        os.makedirs(FNo)

    stfx = sitk.TransformixImageFilter() # stfx instanciated inside loop causes segfault on second execution
    stfx.LogToFileOff()
    stfx.LogToConsoleOff() # no effect if selx.LogToConsoleOn() ?

    ## copy first file as is or transform with identity
    for idx, FN in enumerate(FNs):

        ## skip upto start:
        if(idx < start):
            continue

        FN0= FNs[(idx - 1) % len(FNs)] # http://stackoverflow.com/questions/2167868/getting-next-element-while-cycling-through-a-list#2167962
        FN1= FN
        FNof= FNo + "/" + os.path.splitext(FN1)[0] + ".tif" # TIF for float # http://stackoverflow.com/questions/678236/how-to-get-the-filename-without-the-extension-from-a-path-in-python
        FNt= FNo + "/" + os.path.splitext(FN1)[0] + ".txt"
        DNl= FNo + "/" + os.path.splitext(FN1)[0] + ".log/"

        # Instantiate SimpleElastix
        selx = sitk.ElastixImageFilter() # https://github.com/SuperElastix/SimpleElastix/issues/99#issuecomment-308132783

        selx.LogToFileOff()
        selx.LogToConsoleOn()

        selx.SetParameterMap(selx.ReadParameterFile(args.PF)) # https://github.com/kaspermarstal/SimpleElastix/blob/master/Code/Elastix/include/sitkSimpleElastix.h#L119

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

        print FN0, FN1,
        
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
            tM['InitialTransformParametersFileName'] = [ str(os.path.splitext( FNo + "/" + FNs[(idx - 1) % len(FNs)] )[0] + ".txt") ]

        stfx.AddTransformParameterMap(tM)
        stfx.SetMovingImage(mI)
        with stdout_redirected(): # siclence stfx.Execute()
            stfx.Execute() # stfx instanciated inside loop causes segfault on second execution

        # Write result image
        sitk.WriteImage(sitk.Cast(stfx.GetResultImage(), PixelType), FNof)
        selx.WriteParameterFile(selx.GetTransformParameterMap(0), FNt)


if __name__ == "__main__":
    main()
