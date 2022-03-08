import logging
from multiprocessing.pool import ThreadPool
from typing import Dict, Tuple
from timeit import default_timer as timer
from datetime import timedelta
import monai.deploy.core as md
import numpy as np
from monai.deploy.core import ExecutionContext, InputContext, IOType, Operator, OutputContext


@md.input("image", np.ndarray, IOType.IN_MEMORY)
@md.output("image", np.ndarray, IOType.IN_MEMORY)
@md.output("bounding_box", Tuple, IOType.IN_MEMORY)
@md.env(pip_packages=["monai==0.6.0", "numpy"])
class CropImage(Operator):
    def __init__(self):
        self.logger = logging.getLogger("{}.{}".format(__name__, type(self).__name__))
        super().__init__()
        self.threshold_lower = 1050
        self.threshold_upper = 1100

    def compute(self, op_input: InputContext, op_output: OutputContext, context: ExecutionContext):
        array = op_input.get("image")

        bounding_box = self.get_bounding_box(array)
        cropped_arr = self.crop_array(array, bounding_box)

        logging.info(bounding_box)
        op_output.set(cropped_arr, "image")
        op_output.set(bounding_box, "bounding_box")


    def crop_array(self, array, bounding_box):
        z, y, x = bounding_box
        cropped_arr = array[z[0]:z[1], y[0]: y[1], x[0]: x[1]]

        return cropped_arr

    def get_bounding_box(self, image):
        z = self.get_bound(image, dim=0, padding=10)
        y = self.get_bound(image, dim=1, padding=50)
        x = self.get_bound(image, dim=2, padding=70)
        return z, y, x

    def get_bound(self, arr, dim, padding):
        assert (dim in [0, 1, 2])

        ## Forward
        planes = arr.shape[dim]
        for i in range(planes):
            if dim == 0:
                plane = arr[i, :, :]
            elif dim == 1:
                plane = arr[:, i, :]
            elif dim == 2:
                plane = arr[:, :, i]
            else:
                raise Exception("Cropping condition not met")
            if np.count_nonzero((self.threshold_lower < plane) & (plane < self.threshold_upper)) > 25:
                padded_coord = i - padding
                if padded_coord <= 0:
                    coord1 = 0
                else:
                    coord1 = padded_coord
                break
        else:
            raise Exception("Cropping condition not met")

        ## Backwards
        planes = arr.shape[dim]
        for i in range(arr.shape[dim] - 1, 0, -1):
            if dim == 0:
                plane = arr[i, :, :]
            elif dim == 1:
                plane = arr[:, i, :]
            elif dim == 2:
                plane = arr[:, :, i]
            else:
                raise Exception("Cropping condition not met")
            if np.count_nonzero((self.threshold_lower < plane) & (plane < self.threshold_upper)) > 25:
                padded_coord = i + padding
                if padded_coord >= planes:
                    coord2 = planes
                else:
                    coord2 = padded_coord
                break
        else:
            raise Exception("Cropping condition not met")

        return coord1, coord2

