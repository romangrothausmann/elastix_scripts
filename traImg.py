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
    parser.add_argument("-p", "--paramFile", dest="PF", metavar='ParamFile', required=True, help="Elastix Parameter File")


    args = parser.parse_args()

    # Instantiate SimpleElastix
    selx = sitk.ElastixImageFilter()
    stfx = sitk.TransformixImageFilter()
    selx.LogToFileOff()
    selx.LogToConsoleOn()
    stfx.LogToFileOff()
    stfx.LogToConsoleOn()

    stfx.SetMovingImage(sitk.ReadImage(args.input))
    stfx.SetTransformParameterMap(selx.ReadParameterFile(args.PF))
    stfx.Execute()
    sitk.WriteImage(sitk.Cast(stfx.GetResultImage(), sitk.sitkUInt8), args.output)


if __name__ == "__main__":
    main()
