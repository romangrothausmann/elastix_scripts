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

    mI= sitk.ReadImage(args.input)
    PixelType= mI.GetPixelIDValue()
    
    stfx.SetMovingImage(mI)
    stfx.SetTransformParameterMap(selx.ReadParameterFile(args.PF))
    stfx.SetTransformParameter('Size', map(str, stfx.GetMovingImage().GetSize())) # https://github.com/SuperElastix/SimpleElastix/issues/119#issuecomment-319430741 # https://stackoverflow.com/questions/9525399/python-converting-from-tuple-to-string#9525452
    stfx.Execute()
    sitk.WriteImage(sitk.Cast(stfx.GetResultImage(), PixelType), args.output)


if __name__ == "__main__":
    main()
