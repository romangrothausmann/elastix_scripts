#!/usr/bin/env python3
## https://github.com/kaspermarstal/SimpleElastix/blob/master/Examples/Python/SimpleElastix.py

import itk
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
    rType = itk.Image[itk.F, 2]
    selx = itk.ElastixRegistrationMethod[rType, rType].New()
    stfx = itk.TransformixFilter[rType].New()
    selx.LogToFileOff()
    selx.LogToConsoleOn()
    stfx.LogToFileOff()
    stfx.LogToConsoleOn()

    mI= itk.imread(args.input)
    iType = type(mI)
    mI= itk.cast_image_filter(mI, ttype=(iType, rType)) # ITKElastix needs mType == fType == rType

    ## applying multiple transforms can be done without selx/stfx only using sitk.Resample:
    ## https://github.com/SuperElastix/SimpleElastix/issues/208#issuecomment-400438164
    ## https://github.com/SuperElastix/SimpleElastix/issues/134
    stfx.SetMovingImage(mI)
    tPM= itk.ParameterObject.New()
    tPM.ReadParameterFile(args.PF)
    tPM.SetParameter('Size', map(str, stfx.GetMovingImage().GetLargestPossibleRegion().GetSize())) # https://github.com/SuperElastix/SimpleElastix/issues/119#issuecomment-319430741 # https://stackoverflow.com/questions/9525399/python-converting-from-tuple-to-string#9525452
    stfx.SetTransformParameterObject(tPM)
    stfx.Update()
    itk.imwrite(itk.cast_image_filter(stfx.GetResultImage(), ttype=(rType, iType)), args.output)


if __name__ == "__main__":
    main()
