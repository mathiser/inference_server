import logging

import monai.deploy.core as md
import numpy as np
from monai.deploy.core import ExecutionContext, InputContext, IOType, Operator, OutputContext
from .timer import TimeOP

@md.input("seg", np.ndarray, IOType.IN_MEMORY)
@md.output("seg", np.ndarray, IOType.IN_MEMORY)
@md.env(pip_packages=["monai==0.6.0", "numpy"])
class EndInvertImages(Operator):
    def __init__(self):
        self.logger = logging.getLogger("{}.{}".format(__name__, type(self).__name__))
        super().__init__()

    def compute(self, op_input: InputContext, op_output: OutputContext, context: ExecutionContext):
        """
        This operate inverts seg-array along Z-direction
        :param op_input:
        :param op_output:
        :param context:
        :return:
        """

        timer = TimeOP(__name__)

        seg = op_input.get("seg")
        op_output.set(self.invert(seg), "seg")
        print(timer.report())

    def invert(self, arr):
        return arr[::-1, :, :]