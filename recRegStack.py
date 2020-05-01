#!/usr/bin/env python3
## register a sieries of images concecutively
### register current image to the formerly transformed image
### use InitialTransformParametersFileName (if existant) as InitialTransform
### use case specific ParametersFile (if existant) to changes defaults

## https://github.com/kaspermarstal/SimpleElastix/blob/master/Examples/Python/SimpleElastix.py

import itk
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
    parser.add_argument("-p", "--paramFile", dest="PF", metavar='ParamFile', nargs='+', required=True, help="Elastix Parameter File(s)")
    parser.add_argument("-s", "--start", dest="start", required=False, help="Skip images before specified start-file.")
    parser.add_argument("-S", "--skip", dest="skip", metavar='N', nargs='+', help="Skip specified file-names.")
    parser.add_argument("-f", "--forward", dest="forw", required=False, action='store_true', help="Continue forwards from start-file (-s).")
    parser.add_argument("-b", "--back", dest="back", required=False, action='store_true', help="Continue backwards from start-file (-s).")
    parser.add_argument("-m", "--mask", dest="mask", metavar='boxMask', nargs=4, type=int, help="extent of rectangular mask (xmin, xmax, ymin, ymax).")
    parser.add_argument("-cb", "--checkerboard", dest="cb", nargs=2, type=int, help="create checkerboard image (x-tiles, y-tiles).")
    parser.add_argument("-co", "--compose", dest="co", action='store_true', help="compose images into magenta, green.")
    parser.add_argument("-irpi", "--invertRigidityPenaltyImage", dest="irpi", action='store_true', help="invert TransformRigidityPenalty image.")
    parser.add_argument("-n", "--numberOfThreads", dest="NoT", type=int, help="number of threads used by elastix.")


    args = parser.parse_args()

    FNs= sorted( glob.glob(args.input) ) # http://stackoverflow.com/questions/6773584/how-is-pythons-glob-glob-ordered # http://stackoverflow.com/questions/3207219/how-to-list-all-files-of-a-directory-in-python#3215392
    if args.skip:
        FNs= [x for x in FNs if x not in args.skip] # removing by index (less suitable): [FNs.pop(x) for x in args.skip]
    try:
        start= FNs.index(args.start) # can be used as FNs= FNs[start:] but not ideal for referencing idx-1
    except ValueError:
        start= 0
        if args.start:
            print("Start not found!")
    
    FNo= args.output # FNo= os.path.abspath(FNs[0]) + "/reg/"
    if not os.path.exists(FNo): # http://stackoverflow.com/questions/273192/how-to-check-if-a-directory-exists-and-create-it-if-necessary
        os.makedirs(FNo)

    if args.forw or not args.start:

        ## use previous registered image, if it exists, i.e. continue
        FNp= FNo + "/" + os.path.splitext(FNs[start-1])[0] + ".tif"
        if not os.path.isfile(FNp):
            FNp= None

        ## register series forwards
        register(FNs[start:], FNo, args, FNp) # skip upto start

    if args.back:
    
        ## use previous registered image, if it exists, i.e. continue from forward run
        FNp= FNo + "/" + os.path.splitext(FNs[start])[0] + ".tif"

        ## register series backwards
        register(FNs[start-1::-1], FNo, args, FNp) # backwards from start: https://stackoverflow.com/questions/509211/understanding-pythons-slice-notation#509377

def preProPMs(pMs, FNpF, irpi, mI):
    NpMs= itk.ParameterObject.New() # https://github.com/InsightSoftwareConsortium/ITKElastix/blob/master/examples/2_RegistrationParameters.ipynb
    for i in range(pMs.GetNumberOfParameterMaps()):
        pM= pMs.GetParameterMap(i)
        ## if initial transform parameter file name (not mIT) is provided read it with ITKElastix and insert it as separate pM to workaround bug:
        ## https://github.com/SuperElastix/SimpleElastix/issues/121
        ## works also for stfx which has no SetInitialTransformParameterFileName
        ## https://groups.google.com/forum/#!category-topic/elastix-imageregistration/simpleelastix/TlAbmFE8TPw
        ITpMfn= pMs.GetParameter(i, 'InitialTransformParametersFileName') # ITpMfn is not necessarily FNit
        print(ITpMfn)
        if ITpMfn:
            if ITpMfn != 'NoInitialTransform':
                if os.path.isfile(ITpMfn):
                    NpMs.AddParameterMap(itk.ParameterObject.New().ReadParameterFile(ITpMfn))
                NpMs.AddParameterMap(pM)
                NpMs.SetParameter(i+1, 'InitialTransformParametersFileName', 'NoInitialTransform')
        else:
            NpMs.AddParameterMap(pM)

        ## override default parameter map with individual settings for the current image pair (*.pf.txt)
        if os.path.isfile(FNpF):
            for key, value in itk.ParameterObject.New().ReadParameterFile(FNpF).items():
                pM[key]= value # adds OR replaces existing item: https://stackoverflow.com/questions/6416131/python-add-new-item-to-dictionary#6416157
            print(FNpF),

        # ## auto creation of a RigidityImage
        # if 'Metric' in pM and 'TransformRigidityPenalty' in pM['Metric']: # pM.values():
        #     FNmri= 'MovingRigidityImageName.mha'
        #     if irpi: # inverted
        #         itk.imwrite(1 - itk.rescale_intensity_image_filter(itk.cast_image_filter(mI, ttype=(type(mI), itk.Image[itk.F, 2])), 0, 1), FNmri) # dark in orig. <=> deform less # normalize to [0;1]
        #     else: # not inverted
        #         itk.imwrite(itk.rescale_intensity_image_filter(itk.cast_image_filter(mI, ttype=(type(mI), itk.Image[itk.F, 2])), 0, 1), FNmri) # normalize to [0;1]
        #     pM['MovingRigidityImageName']= [FNmri]
    return(NpMs)

def register(FNs, FNo, args, FNp= None):
    rI= None
    for idx, FN in enumerate(FNs):
        FN0= FNs[(idx - 1) % len(FNs)] # http://stackoverflow.com/questions/2167868/getting-next-element-while-cycling-through-a-list#2167962
        FN1= FN

        FNof= FNo + "/" + os.path.splitext(FN1)[0] + ".tif" # TIF for float # http://stackoverflow.com/questions/678236/how-to-get-the-filename-without-the-extension-from-a-path-in-python
        FNit= os.path.splitext(FN1)[0] + ".txt"
        FNpF= os.path.splitext(FN1)[0] + ".pf.txt" # selx.ReadParameterFile expects *.txt
        FNt1= FNo + "/" + os.path.splitext(FN1)[0] + ".txt"
        DNl = FNo + "/" + os.path.splitext(FN1)[0] + ".log/"

        # Instantiate ITKElastix
        rType = itk.Image[itk.F, 2]
        selx = itk.ElastixRegistrationMethod[rType, rType].New() # https://itkpythonpackage.readthedocs.io/en/latest/Quick_start_guide.html#instantiate-an-itk-object
        selx.LogToFileOff()
        selx.LogToConsoleOn()
        if args.NoT:
            selx.SetNumberOfThreads(args.NoT)

        ## combine/append parameter maps for e.g. different transforms:
        ## http://simpleelastix.readthedocs.io/NonRigidRegistration.html
        ## http://simpleelastix.readthedocs.io/ParameterMaps.html
        pMs= itk.ParameterObject.New() # https://github.com/InsightSoftwareConsortium/ITKElastix/blob/master/examples/2_RegistrationParameters.ipynb
        pMs.ReadParameterFile(args.PF) # reads multiple PFs! https://github.com/InsightSoftwareConsortium/ITKElastix/blob/8987e97c85983a2c99947b85b1e79301d38e0185/examples/2_RegistrationParameters.ipynb?short_path=3d874bd#L873

        if not os.path.exists(DNl):
            os.makedirs(DNl)
        selx.SetOutputDirectory(DNl)

        elastixLog= os.path.splitext(FN1)[0] + ".log"
        selx.SetLogFileName(elastixLog)
        elastixLogPath= DNl + elastixLog

        print("%5.1f%% (%d/%d)" % ((idx+1) * 100.0 / len(FNs), idx+1, len(FNs))),
        sys.stdout.flush() # essential with \r !

        mI= itk.imread(FN1)
        iType = type(mI)
        mI= itk.cast_image_filter(mI, ttype=(iType, rType)) # ITKElastix needs mType == fType == rType

        if idx == 0:
            if FNp and os.path.exists(FNp): # exists() fails on None
                FN0=FNp
            else:
                itk.imwrite(itk.cast_image_filter(mI, ttype=(rType, iType)), FNof)
                print(FN1, FNof, "plain copy")
                continue
        else:
            FN0= FNo + "/" + os.path.splitext(FN0)[0] + ".tif"

        if rI:
            fI= rI # reuse last rI (avoid re-read)
        else:
            fI= itk.imread(FN0)
            fI= itk.cast_image_filter(fI, ttype=(type(fI), rType)) # ITKElastix needs mType == fType == rType

        print(FN0, FN1),

        selx.SetFixedImage(fI) # https://github.com/kaspermarstal/SimpleElastix/blob/master/Code/IO/include/sitkImageFileReader.h#L73
        selx.SetMovingImage(mI)
        selx.SetParameterObject(preProPMs(pMs, FNpF, args.irpi, mI))

        if args.mask:
            fM= itk.Image(fI.GetSize(), itk.UC) # init with 0 acc. to docs
            fM.CopyInformation(fI) # essential for selx
            xmin= args.mask[0]
            xmax= args.mask[1]
            ymin= args.mask[2]
            ymax= args.mask[3]
            mR= fM[xmin:xmax, ymin:ymax] == 0
            fM= itk.paste_image_filter(fM, mR, list(mR.GetSize()), [0, 0], list(map(int, mR.GetOrigin())))
            fM= itk.mask_negated_image_filter(fM, fI) # also disregard empty regions in fI
            selx.SetFixedMask(itk.cast_image_filter(fM, ttype=(rType, itk.Image[itk.UC, 2])))
            # itk.imwrite(fM, "fM_%03d.tif" % idx);
        else:
            selx.SetFixedMask(itk.cast_image_filter(fI, ttype=(rType, itk.Image[itk.UC, 2])))

        ## set initial transform parameter file name for mIT (not effected by bug: https://github.com/SuperElastix/SimpleElastix/issues/121)
        if os.path.isfile(FNit):
            selx.SetInitialTransformParameterFileName(FNit)
            print(selx.GetInitialTransformParameterFileName()),

        with open(elastixLogPath, 'w') as f, stdout_redirected(f):
            selx.Update()
        f.close()

        fMV= []
        fMVs= []
        cfMV= None
        nM= None
        mN= pMs.GetNumberOfParameterMaps() - 1 # reverse parsing, so start with last pM
        with open(elastixLogPath) as f:
            for line in reversed(f.readlines()): # "Final metric value" reported after table # https://stackoverflow.com/a/2301792
                if not cfMV: # get "Final metric value" (fMV)
                    m= re.search('Final metric value  = (?P<value>[-\+\.0-9]+)', line) # normally: - has to be first and +. need escaping, dyn. length # http://lists.bigr.nl/pipermail/elastix/2016-December/002435.html
                    if m:
                        try:
                            cfMV= m.group('value')
                        except:
                            raise Exception('Final metric value not found in "elastix.log".')
                        fMV.append(cfMV)
                        nM= len(pMs.GetParameter(0, 'Metric')) # number of metrices, avoids to get nM from tabel headers
                else: # get line of fMV in table
                    cols= line.split()
                    if len(cols) > 1 and cols[0].isdigit(): # test if first col/word is an integer (last iter of table)
                        if nM > 1:
                            fMVs.append(cols[0:nM+2]) # overall metric and each individual metric
                        else:
                            fMVs.append(cols[0:nM+1]) # only overall metric
                        cfMV= None # continue for next transform
                        mN-=1 # previous pM
        f.close()
        for i in range(pMs.GetNumberOfParameterMaps()-1, -1, -1):
            print(fMVs[i][0], fMV[i], fMVs[i][1:]),
        print()

        # Write result image
        rI= selx.GetOutput()
        itk.imwrite(itk.cast_image_filter(rI, ttype=(rType, iType)), FNof) # include cast to be comparable to those read from disk
        # selx.WriteParameterFile(selx.GetTransformParameterMap(0), FNt1) # written by elastix (in more detail) to: DNl + "/TransformParameters.0.txt"

        if args.cb or args.co:
            sfI= itk.cast_image_filter(itk.shift_scale_image_filter(itk.normalize_image_filter(itk.cast_image_filter(fI, ttype=(iType, rType))) * -1, 256/2, 1.99), ttype=(rType, iType)) # VERY sensitive to scale factor! first shifts then scales!
            smI= itk.cast_image_filter(itk.shift_scale_image_filter(itk.normalize_image_filter(selx.GetResultImage()) * -1, 256/2, 1.99), ttype=(rType, iType)) # VERY sensitive to scale factor! first shifts then scales!
        
        if args.cb:
            itk.imwrite(itk.checker_board_image_filter(sfI, smI, args.cb), FNof.replace(".tif", "_cb.png"))
            
        if args.co:
            itk.imwrite(itk.compose_image_filter(sfI, smI, sfI//2.+smI//2.), FNof.replace(".tif", "_co.png"))

if __name__ == "__main__":
    main()
