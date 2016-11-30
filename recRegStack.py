## https://github.com/kaspermarstal/SimpleElastix/blob/master/Examples/Python/SimpleElastix.py

import SimpleITK as sitk
import sys
import os
import glob

# Instantiate SimpleElastix
selx = sitk.SimpleElastix()
stfx = sitk.SimpleTransformix()
selx.LogToConsoleOff()
stfx.LogToConsoleOff()

selx.SetParameterMap(selx.ReadParameterFile(str(sys.argv[3]))) # https://github.com/kaspermarstal/SimpleElastix/blob/master/Code/Elastix/include/sitkSimpleElastix.h#L119
selx.PrintParameterMap()

FNs= glob.glob(sys.argv[1]) # http://stackoverflow.com/questions/3207219/how-to-list-all-files-of-a-directory-in-python#3215392
FNo= sys.argv[2] # FNo= os.path.abspath(FNs[0]) + "/reg/"
if not os.path.exists(FNo): # http://stackoverflow.com/questions/273192/how-to-check-if-a-directory-exists-and-create-it-if-necessary
    os.makedirs(FNo)

## copy first file as is or transform with identity

for idx, FN in enumerate(FNs):
    FN0= FNs[(idx - 1) % len(FNs)] # http://stackoverflow.com/questions/2167868/getting-next-element-while-cycling-through-a-list#2167962
    FN1= FN
    FNof= sys.argv[2] + "/" + os.path.splitext(FN1)[0] + ".tif" # TIF for float # http://stackoverflow.com/questions/678236/how-to-get-the-filename-without-the-extension-from-a-path-in-python
    FNt= sys.argv[2] + "/" + os.path.splitext(FN1)[0] + ".txt"

    print("\r%5.1f%% (%d/%d)" % ((idx+1) * 100.0 / len(FNs), idx+1, len(FNs))),
    sys.stdout.flush() # essential with \r !
    
    if idx == 0:
        sitk.WriteImage(sitk.Cast(sitk.ReadImage(FN1), sitk.sitkUInt8), FNof)
        continue

    fI= sitk.ReadImage(FN0)
    mI= sitk.ReadImage(FN1)

    selx.SetFixedImage(fI) # https://github.com/kaspermarstal/SimpleElastix/blob/master/Code/IO/include/sitkImageFileReader.h#L73
    selx.SetMovingImage(mI)
    selx.Execute()

    tM= selx.GetTransformParameterMap(0)
    if idx > 1:
        tM['InitialTransformParametersFileName'] = [ str(os.path.splitext( sys.argv[2] + "/" + FNs[(idx - 1) % len(FNs)] )[0] + ".txt") ]

    stfx.AddTransformParameterMap(tM)
    stfx.SetMovingImage(mI)
    stfx.Execute()

    # Write result image
    sitk.WriteImage(sitk.Cast(stfx.GetResultImage(), sitk.sitkUInt8), FNof)
    selx.WriteParameterFile(selx.GetTransformParameterMap(0), FNt)

