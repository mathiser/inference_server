import logging
import os
import shutil
import tempfile
from multiprocessing.pool import ThreadPool
from typing import Dict

import SimpleITK as sitk
import monai.deploy.core as md
import numpy as np
from monai.deploy.core import ExecutionContext, InputContext, IOType, Operator, OutputContext


@md.input("image", np.ndarray, IOType.IN_MEMORY)
@md.input("ref_image", sitk.Image, IOType.IN_MEMORY)
@md.output("seg", np.ndarray, IOType.IN_MEMORY)
@md.env(pip_packages=["monai==0.6.0", "simpleitk", "numpy", "nnunet"])
class PredictImage(Operator):
    def __init__(self):
        self.logger = logging.getLogger("{}.{}".format(__name__, type(self).__name__))
        super().__init__()

    def compute(self, op_input: InputContext, op_output: OutputContext, context: ExecutionContext):

        array = op_input.get("image")
        ref_image = op_input.get("ref_image")
        tmp_in = tempfile.mkdtemp()
        tmp_out = tempfile.mkdtemp()

        tmp_img = sitk.GetImageFromArray(array)
        tmp_img.SetSpacing(ref_image.GetSpacing())
        sitk.WriteImage(tmp_img, os.path.join(tmp_in, "tmp_0000.nii.gz"))

        os.system(f"nnUNet_predict -i {tmp_in} -o {tmp_out} -t 5002")

        for f in os.listdir(tmp_out):
            if f.endswith(".nii.gz"):
                pred_img = sitk.ReadImage(os.path.join(tmp_out, f))
                pred_arr = sitk.GetArrayFromImage(pred_img)
                op_output.set(pred_arr, "seg")
                shutil.rmtree(tmp_in)
                shutil.rmtree(tmp_out)
                break
        else:
            raise Exception("No prediction found")