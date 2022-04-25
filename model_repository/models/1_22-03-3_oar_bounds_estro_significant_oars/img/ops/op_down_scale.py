import logging
from multiprocessing.pool import ThreadPool
from typing import Dict, Tuple

import monai.deploy.core as md
import numpy as np
import skimage.measure
from monai.deploy.core import ExecutionContext, InputContext, IOType, Operator, OutputContext, Image
import SimpleITK as sitk
from .timer import TimeOP

@md.input("label_array_dict", Dict[str, np.ndarray], IOType.IN_MEMORY)
@md.input("ref_image", sitk.Image, IOType.IN_MEMORY)
@md.output("label_array_dict", Dict[str, np.ndarray], IOType.IN_MEMORY)
@md.output("scale_factor", Tuple, IOType.IN_MEMORY)
@md.env(pip_packages=["monai==0.6.0", "simpleitk", "numpy", "scikit-image"])
class DownScaleImages(Operator):
    def __init__(self):
        self.logger = logging.getLogger("{}.{}".format(__name__, type(self).__name__))
        super().__init__()

    def compute(self, op_input: InputContext, op_output: OutputContext, context: ExecutionContext):
        timer = TimeOP(__name__)

        arrs = op_input.get("label_array_dict")
        ref_img = op_input.get("ref_image")
        ref_arr = sitk.GetArrayFromImage(ref_img)
        ref_dim = ref_arr.shape

        scale_factor = self.get_scale_factor(arrs["tmp_0001.nii.gz"], ref_dim)
        op_output.set(scale_factor, "scale_factor")
        arrs["tmp_0001.nii.gz"] = self.down_scale(arrs["tmp_0001.nii.gz"], scale_factor)
        op_output.set(arrs, label="label_array_dict")

        print(timer.report())

    def get_scale_factor(self, img_arr, ref_dim):
        scale_factor = tuple(np.array(img_arr.shape) // np.array(ref_dim))
        logging.info(scale_factor)
        return scale_factor

    def down_scale(self, img_arr, scale_factor: Tuple):
        reduced_arr = skimage.measure.block_reduce(img_arr, scale_factor, np.max)
        return reduced_arr
