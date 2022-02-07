import logging
import os.path

import SimpleITK as sitk
import monai.deploy.core as md
import numpy as np
from monai.deploy.core import ExecutionContext, DataPath, InputContext, IOType, Operator, OutputContext


@md.input("seg", np.ndarray, IOType.IN_MEMORY)
@md.input("ref_image", sitk.Image, IOType.IN_MEMORY)
@md.output("", DataPath, IOType.DISK)
@md.env(pip_packages=["monai==0.6.0", "simpleitk", "numpy"])

class SegmentationWriter(Operator):
    def __init__(self):
        self.logger = logging.getLogger("{}.{}".format(__name__, type(self).__name__))
        super().__init__()

    def compute(self, op_input: InputContext, op_output: OutputContext, context: ExecutionContext):
        arr = op_input.get("seg")
        ref_img = op_input.get("ref_image")
        out_path = op_output.get().path

        img = sitk.GetImageFromArray(arr)
        img.SetSpacing(ref_img.GetSpacing())
        sitk.WriteImage(img, os.path.join(out_path, "segmentation.nii.gz"))