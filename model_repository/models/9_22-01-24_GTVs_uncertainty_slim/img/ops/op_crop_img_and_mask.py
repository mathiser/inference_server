import logging
from multiprocessing.pool import ThreadPool
from typing import Dict, Tuple

import monai.deploy.core as md
import numpy as np
from monai.deploy.core import ExecutionContext, InputContext, IOType, Operator, OutputContext
from .timer import TimeOP

@md.input("label_array_dict", Dict[str, np.ndarray], IOType.IN_MEMORY)
@md.output("label_array_dict", Dict[str, np.ndarray], IOType.IN_MEMORY)
@md.output("bounding_box", Tuple, IOType.IN_MEMORY)
@md.env(pip_packages=["monai==0.6.0", "numpy"])
class CropAllImages(Operator):
    def __init__(self):
        self.logger = logging.getLogger("{}.{}".format(__name__, type(self).__name__))
        super().__init__()

    def compute(self, op_input: InputContext, op_output: OutputContext, context: ExecutionContext):
        timer = TimeOP(__name__)

        label_array_dict = op_input.get("label_array_dict")

        for k in label_array_dict.keys():
            if "0002" in k:
                mr_key = k
                break
        else:
            raise Exception("0002 MR not found")
        bounding_box = self.get_bounding_box(label_array_dict[mr_key]) ## T1 MRI bbox of non-zero
        logging.info(bounding_box)

        t = ThreadPool(4)
        results = t.starmap(self.crop_array, self.arg_yield(label_array_dict, bounding_box))
        t.close()
        t.join()

        op_output.set({t[0]: t[1] for t in results}, "label_array_dict")
        op_output.set(bounding_box, "bounding_box")
        print(timer.report())

    def crop_array(self, label, array, bounding_box):
        z, y, x = bounding_box
        cropped_arr = array[z[0]:z[1], y[0]: y[1], x[0]: x[1]]

        return label, cropped_arr



    def arg_yield(self, label_array_dict, bounding_box):
        for label, array in label_array_dict.items():
            yield (label, array, bounding_box)

    def get_bounding_box(self, array):

        z = self.get_bound(array, dim=0, padding=0)
        y = self.get_bound(array, dim=1, padding=0)
        x = self.get_bound(array, dim=2, padding=0)
        return (z, y, x)

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

            if np.count_nonzero(plane) != 0:
                padded_coord = i - padding
                if padded_coord <= 0:
                    coord1 = 0
                else:
                    coord1 = padded_coord
                break

        ## Backwards
        planes = arr.shape[dim]
        for i in range(arr.shape[dim] - 1, 0, -1):
            if dim == 0:
                plane = arr[i, :, :]
            elif dim == 1:
                plane = arr[:, i, :]
            elif dim == 2:
                plane = arr[:, :, i]

            if np.count_nonzero(plane) != 0:
                padded_coord = i + padding
                if padded_coord >= planes:
                    coord2 = planes
                else:
                    coord2 = padded_coord
                break
        return coord1, coord2