#!/usr/bin/env python2
## https://github.com/kaspermarstal/SimpleElastix/blob/master/Examples/Python/SimpleElastix.py

import SimpleITK as sitk
import sys
import argparse

def main():
    
    usage_text =  "Run SimpleElastix sequentially on series images:"
    usage_text +=  __file__ + " [options]"
    
    parser = argparse.ArgumentParser(description=usage_text)

    parser.add_argument("-i", "--input", dest="input", metavar='GlobPattern', required=True, help="Glob-pattern for input files.")
    parser.add_argument("-o", "--output", dest="output", metavar='DestDir', required=True, help="Output dir to save the result images in.")
    parser.add_argument("-p", "--paramFile", dest="PF", metavar='ParamFile', nargs='+', required=True, help="Elastix Parameter File")


    args = parser.parse_args()

    # Instantiate SimpleElastix
    selx = sitk.ElastixImageFilter()
    stfx = sitk.TransformixImageFilter()
    selx.LogToFileOff()
    selx.LogToConsoleOn()
    stfx.LogToFileOff()
    stfx.LogToConsoleOn()

    mI= sitk.ReadImage(args.input)
    PixelType= mI.GetPixelIDValue()

    ## applying multiple transforms can be done without selx/stfx only using sitk.Resample:
    ## https://github.com/SuperElastix/SimpleElastix/issues/208#issuecomment-400438164
    ## https://github.com/SuperElastix/SimpleElastix/issues/134
    stfx.SetMovingImage(mI)
    
    pMs= sitk.VectorOfParameterMap() # https://github.com/SuperElastix/SimpleElastix/blob/2a79d151894021c66dceeb2c8a64ff61506e7155/Wrapping/Common/SimpleITK_Common.i#L211
    for pf in args.PF:
        pM= selx.ReadParameterFile(pf)
        # selx.PrintParameterMap(pM)
        pMs.append(pM)
    stfx.SetTransformParameterMap(pMs)

    ## set output size to input size if not specified in any PF
    if any('Size' in pM for pM in pMs): # https://stackoverflow.com/questions/14790980/how-can-i-check-if-key-exists-in-list-of-dicts-in-python#14790997
        size= next(pM for i,pM in enumerate(pMs) if 'Size' in pM)['Size']
    else:
        size= map(str, stfx.GetMovingImage().GetSize()) # https://github.com/SuperElastix/SimpleElastix/issues/119#issuecomment-319430741 # https://stackoverflow.com/questions/9525399/python-converting-from-tuple-to-string#9525452
    stfx.SetTransformParameter('Size', size)

    stfx.Execute()
    sitk.WriteImage(sitk.Cast(stfx.GetResultImage(), PixelType), args.output)


if __name__ == "__main__":
    main()
