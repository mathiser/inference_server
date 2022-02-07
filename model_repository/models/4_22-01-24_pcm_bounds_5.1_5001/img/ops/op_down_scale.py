import logging
from multiprocessing.pool import ThreadPool
from typing import Dict

import monai.deploy.core as md
import numpy as np
import skimage.measure
from monai.deploy.core import ExecutionContext, InputContext, IOType, Operator, OutputContext, Image
import SimpleITK as sitk
from .timer import TimeOP

@md.input("label_array_dict", Dict[str, np.ndarray], IOType.IN_MEMORY)
@md.input("ref_image", sitk.Image, IOType.IN_MEMORY)
@md.output("label_array_dict", Dict[str, np.ndarray], IOType.IN_MEMORY)
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

        t = ThreadPool(4)
        results = t.starmap(self.down_scale, self.arg_yield(arrs, ref_dim))
        t.close()
        t.join()
        op_output.set({t[0]: t[1] for t in results}, label="label_array_dict")
        print(timer.report())

    def arg_yield(self, arrs, ref_dim):
        for label, arr in arrs.items():
            yield (label, arr, ref_dim)

    def down_scale(self, label, img_arr, ref_dim):
        scale_factor = np.array(img_arr.shape) // np.array(ref_dim)
        logging.info(f"Scale factor: {scale_factor}")

        reduced_arr = skimage.measure.block_reduce(img_arr, tuple(scale_factor), np.max)

        logging.info(f"Reduced image has dimentions arr:{reduced_arr.shape}")
        return (label, reduced_arr)
