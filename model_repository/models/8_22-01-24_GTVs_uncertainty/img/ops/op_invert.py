import logging
from multiprocessing.pool import ThreadPool
from typing import Dict

import monai.deploy.core as md
import numpy as np
from monai.deploy.core import ExecutionContext, InputContext, IOType, Operator, OutputContext
from .timer import TimeOP

@md.input("label_array_dict", Dict[str, np.ndarray], IOType.IN_MEMORY)
@md.output("label_array_dict", Dict[str, np.ndarray], IOType.IN_MEMORY)
@md.env(pip_packages=["monai==0.6.0", "numpy"])
class InvertImages(Operator):
    def __init__(self):
        self.logger = logging.getLogger("{}.{}".format(__name__, type(self).__name__))

        super().__init__()

    def compute(self, op_input: InputContext, op_output: OutputContext, context: ExecutionContext):
        """
        This operator flipped all arrays in label_array_dict along the z-direction

        :param op_input:
        :param op_output:
        :param context:
        :return:
        """
        timer = TimeOP(__name__)
        label_array_dict = op_input.get("label_array_dict")

        t = ThreadPool(4)
        results = t.starmap(self.invert, label_array_dict.items())
        t.close()
        t.join()

        op_output.set({t[0]: t[1] for t in results}, "label_array_dict")
        print(timer.report())

    def invert(self, label, arr):
        return (label, arr[::-1, :, :])