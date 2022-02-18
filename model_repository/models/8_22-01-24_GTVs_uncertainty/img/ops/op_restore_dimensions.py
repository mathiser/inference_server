import logging
from typing import Tuple

import SimpleITK as sitk
import monai.deploy.core as md
import numpy as np
from monai.deploy.core import ExecutionContext, InputContext, IOType, Operator, OutputContext
from monai.transforms import Pad
from .timer import TimeOP
@md.input("seg", np.ndarray, IOType.IN_MEMORY)
@md.input("ref_image", sitk.Image, IOType.IN_MEMORY)
@md.input("bounding_box", Tuple, IOType.IN_MEMORY)
@md.output("seg", np.ndarray, IOType.IN_MEMORY)
@md.env(pip_packages=["monai==0.6.0", "simpleitk", "numpy"])
class RestoreDimensions(Operator):
    def __init__(self):
        self.logger = logging.getLogger("{}.{}".format(__name__, type(self).__name__))
        super().__init__()

    def compute(self, op_input: InputContext, op_output: OutputContext, context: ExecutionContext):
        timer = TimeOP(__name__)

        seg_arr = op_input.get("seg")
        ref_image = op_input.get("ref_image")
        ref_image_arr = sitk.GetArrayFromImage(ref_image)

        bounding_box = op_input.get("bounding_box")

        z, y, x = bounding_box
        logging.info(f"Bounding box: {bounding_box}")
        logging.info(f"Reference array shape: {ref_image_arr.shape}")

        full_arr = np.zeros_like(ref_image_arr)
        logging.info(f"Full size array size: {full_arr.shape}")
        full_arr[z[0]:z[1], y[0]:y[1], x[0]:x[1]] = seg_arr

        op_output.set(full_arr, "seg")
        print(timer.report())

    # def compute(self, op_input: InputContext, op_output: OutputContext, context: ExecutionContext):
    #     seg_arr = op_input.get("seg")
    #     ref_image = op_input.get("ref_image")
    #     ref_image_arr = sitk.GetArrayFromImage(ref_image)
    #
    #     bounding_box = op_input.get("bounding_box")
    #
    #     z, y, x = bounding_box
    #     logging.info(f"Bounding box: {bounding_box}")
    #     logging.info(f"Reference array shape: {ref_image_arr.shape}")
    #     arr_shape = ref_image_arr.shape
    #     padding = [(x[0], arr_shape[2] - x[1]),
    #                (y[0], arr_shape[1] - y[1]),
    #                (z[0], arr_shape[0] - z[1])]
    #
    #     padder = Pad(padding, "constant")
    #     padded_arr = padder(seg_arr)
    #     op_output.set(padded_arr, "seg")
    #     print("with monai Pad")
    #     print(self.timer.report())
