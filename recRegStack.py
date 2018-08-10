#!/usr/bin/env python2
## register a sieries of images concecutively
### register current image to the formerly transformed image
### use InitialTransformParametersFileName (if existant) as InitialTransform
### use case specific ParametersFile (if existant) to changes defaults

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
    except ValueError, e:
        start= 0
        if args.start:
            print "Start not found!"
    
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


def register(FNs, FNo, args, FNp= None):
    for idx, FN in enumerate(FNs):
        FN0= FNs[(idx - 1) % len(FNs)] # http://stackoverflow.com/questions/2167868/getting-next-element-while-cycling-through-a-list#2167962
        FN1= FN

        FNof= FNo + "/" + os.path.splitext(FN1)[0] + ".tif" # TIF for float # http://stackoverflow.com/questions/678236/how-to-get-the-filename-without-the-extension-from-a-path-in-python
        FNit= os.path.splitext(FN1)[0] + ".txt"
        FNpF= os.path.splitext(FN1)[0] + ".pf.txt" # selx.ReadParameterFile expects *.txt
        FNt1= FNo + "/" + os.path.splitext(FN1)[0] + ".txt"
        DNl = FNo + "/" + os.path.splitext(FN1)[0] + ".log/"

        # Instantiate SimpleElastix
        selx = sitk.ElastixImageFilter() # https://github.com/SuperElastix/SimpleElastix/issues/99#issuecomment-308132783
        selx.LogToFileOff()
        selx.LogToConsoleOn()
        if args.NoT:
            selx.SetNumberOfThreads(args.NoT)

        ## combine/append parameter maps for e.g. different transforms:
        ## http://simpleelastix.readthedocs.io/NonRigidRegistration.html
        ## http://simpleelastix.readthedocs.io/ParameterMaps.html
        pMs= sitk.VectorOfParameterMap() # https://github.com/SuperElastix/SimpleElastix/blob/2a79d151894021c66dceeb2c8a64ff61506e7155/Wrapping/Common/SimpleITK_Common.i#L211
        for pf in args.PF:
            pMs.append(selx.ReadParameterFile(pf)) # https://github.com/SuperElastix/SimpleElastix/blob/master/Code/Elastix/include/sitkElastixImageFilter.h#L119

        if not os.path.exists(DNl):
            os.makedirs(DNl)
        selx.SetOutputDirectory(DNl)

        elastixLog= os.path.splitext(FN1)[0] + ".log"
        selx.SetLogFileName(elastixLog)
        elastixLogPath= DNl + elastixLog

        print("%5.1f%% (%d/%d)" % ((idx+1) * 100.0 / len(FNs), idx+1, len(FNs))),
        sys.stdout.flush() # essential with \r !

        otsu= sitk.OtsuThresholdImageFilter()
        otsu.SetInsideValue(0)
        otsu.SetOutsideValue(1)
        smdm= sitk.SignedMaurerDistanceMapImageFilter()
        smdm.SquaredDistanceOff()
        smdm.UseImageSpacingOff()

        mI= sitk.ReadImage(FN1)
        PixelType= mI.GetPixelIDValue()

        mIod= otsu.Execute(mI)
        mIod= smdm.Execute(mIod) # sitk.SignedMaurerDistanceMap(mI, squaredDistance=False, useImageSpacing=False)

        if idx == 0:
            if FNp and os.path.exists(FNp): # exists() fails on None
                FN0=FNp
            else:
                sitk.WriteImage(sitk.Cast(mI, PixelType), FNof)
                print FN1, FNof, "plain copy"
                continue
        else:
            FN0= FNo + "/" + os.path.splitext(FN0)[0] + ".tif"

        fI= sitk.ReadImage(FN0)
        fIod= otsu.Execute(fI)
        fIod= smdm.Execute(fIod)

        print FN0, FN1,

        selx.SetFixedImage(fIod) # https://github.com/kaspermarstal/SimpleElastix/blob/master/Code/IO/include/sitkImageFileReader.h#L73
        selx.SetMovingImage(mIod)

        for i, pM in enumerate(pMs):
            pMs[i].erase('InitialTransformParametersFileName')

            if os.path.isfile(FNpF):
                # pM.asdict().update(selx.ReadParameterFile(FNpF).asdict()) # no effect: https://github.com/SuperElastix/SimpleElastix/issues/169
                for key, value in selx.ReadParameterFile(FNpF).items():
                    pM[key]= value # adds OR replaces existing item: https://stackoverflow.com/questions/6416131/python-add-new-item-to-dictionary#6416157
                pMs[i]= pM # apparently only a complete pM can be assigned to pMs, not idividual key-value-pairs like pMs[0][key]= value; pM is a copy! https://stackoverflow.com/questions/13752461/python-how-to-change-values-in-a-list-of-lists#13752588
                print FNpF,

            if 'TransformRigidityPenalty' in pM['Metric']: # pM.values():
                FNmri= 'MovingRigidityImageName.mha'
                if args.irpi:
                    sitk.WriteImage(1 - sitk.RescaleIntensity(sitk.Cast(mI, sitk.sitkFloat32), 0, 1), FNmri) # dark in orig. <=> deform less # normalize to [0;1]
                else:
                    sitk.WriteImage(sitk.RescaleIntensity(sitk.Cast(mI, sitk.sitkFloat32), 0, 1), FNmri) # normalize to [0;1]
                pM['MovingRigidityImageName']= [FNmri]
                pMs[i]= pM # pM is a copy! https://stackoverflow.com/questions/13752461/python-how-to-change-values-in-a-list-of-lists#13752588

        selx.SetParameterMap(pMs)

        if args.mask:
            fM= sitk.Image(fI.GetSize(), sitk.sitkUInt8) # init with 0 acc. to docs
            fM.CopyInformation(fI) # essential for selx
            xmin= args.mask[0]
            xmax= args.mask[1]
            ymin= args.mask[2]
            ymax= args.mask[3]
            mR= fM[xmin:xmax, ymin:ymax] == 0
            fM= sitk.Paste(fM, mR, list(mR.GetSize()), [0, 0], list(map(int, mR.GetOrigin())))
            fM= fM & (fI != 0) # also disregard empty regions in fI
            selx.SetFixedMask(fM)
            # sitk.WriteImage(fM, "fM_%03d.tif" % idx);
        else:
            selx.SetFixedMask(fI != 0)

        if os.path.isfile(FNit):
            selx.SetInitialTransformParameterFileName(FNit)
            print selx.GetInitialTransformParameterFileName(),
        with open(elastixLogPath, 'w') as f, stdout_redirected(f):
            selx.Execute()
        f.close()

        fMV= []
        fMVs= []
        cfMV= None
        nM= None
        mN= len(pMs)-1 # reverse parsing, so start with last pM
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
                        nM= len(pMs[mN]['Metric']) # number of metrices, avoids to get nM from tabel headers
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
        for i in range(len(pMs)-1,-1,-1):
            print fMVs[i][0], fMV[i], fMVs[i][1:],
        print

        # Write result image
        stfx = sitk.TransformixImageFilter()
        stfx.LogToFileOff()
        stfx.LogToConsoleOff()
        stfx.SetMovingImage(mI)
        stfx.SetTransformParameterMap(selx.GetTransformParameterMap())
        stfx.Execute()
        sitk.WriteImage(sitk.Cast(stfx.GetResultImage(), PixelType), FNof)
        # selx.WriteParameterFile(selx.GetTransformParameterMap(0), FNt1) # written by elastix (in more detail) to: DNl + "/TransformParameters.0.txt"

        if args.cb or args.co:
            sfI= sitk.Cast(sitk.ShiftScale(sitk.Normalize(sitk.Cast(fI, sitk.sitkFloat32)) * -1, 256/2, 1.99), sitk.sitkUInt8) # VERY sensitive to scale factor! first shifts then scales!
            smI= sitk.Cast(sitk.ShiftScale(sitk.Normalize(selx.GetResultImage()) * -1, 256/2, 1.99), sitk.sitkUInt8) # VERY sensitive to scale factor! first shifts then scales!
        
        if args.cb:
            sitk.WriteImage(sitk.CheckerBoard(sfI, smI, args.cb), FNof.replace(".tif", "_cb.png"))
            
        if args.co:
            sitk.WriteImage(sitk.Compose(sfI, smI, sfI//2.+smI//2.), FNof.replace(".tif", "_co.png"))

if __name__ == "__main__":
    main()
