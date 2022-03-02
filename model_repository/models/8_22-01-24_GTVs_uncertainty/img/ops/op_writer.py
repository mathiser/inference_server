import logging
import os.path

import SimpleITK as sitk
import monai.deploy.core as md
import numpy as np
from monai.deploy.core import ExecutionContext, DataPath, InputContext, IOType, Operator, OutputContext
from .timer import TimeOP

@md.input("seg", np.ndarray, IOType.IN_MEMORY)
@md.input("ref_image", sitk.Image, IOType.IN_MEMORY)
@md.output("", DataPath, IOType.DISK)
@md.env(pip_packages=["monai==0.6.0", "simpleitk", "numpy"])

class DataWriter(Operator):
    def __init__(self):
        self.logger = logging.getLogger("{}.{}".format(__name__, type(self).__name__))
        super().__init__()

    def compute(self, op_input: InputContext, op_output: OutputContext, context: ExecutionContext):
        """
        This operator saves the final segmentation in segmentation.nii.gz. This is eventually zipped by the inference server
        and sent back to MIM.

        :param op_input:
        :param op_output:
        :param context:
        :return:
        """
        timer = TimeOP(__name__)

        arr = op_input.get("seg")
        out_path = op_output.get().path

        img = sitk.GetImageFromArray(arr)
        sitk.WriteImage(img, os.path.join(out_path, "segmentation.nii.gz"))
        print(timer.report())
