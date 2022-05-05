import logging
from typing import Tuple

import monai.deploy.core as md
import numpy as np
from monai.deploy.core import ExecutionContext, InputContext, IOType, Operator, OutputContext

from .timer import TimeOP
@md.input("seg", np.ndarray, IOType.IN_MEMORY)
@md.input("scale_factor", Tuple, IOType.IN_MEMORY)
@md.output("seg", np.ndarray, IOType.IN_MEMORY)
@md.env(pip_packages=["monai==0.6.0", "numpy"])
class Upscale(Operator):
    def __init__(self):
        self.logger = logging.getLogger("{}.{}".format(__name__, type(self).__name__))

        super().__init__()

    def compute(self, op_input: InputContext, op_output: OutputContext, context: ExecutionContext):
        timer = TimeOP(__name__)
        scaling_factor = op_input.get("scale_factor")
        seg = op_input.get("seg")
        up_scaled_seg = np.kron(seg, np.ones(scaling_factor))
        op_output.set(up_scaled_seg, "seg")

        print(timer.report())
