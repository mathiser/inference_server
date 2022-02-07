import logging
from multiprocessing.pool import ThreadPool
from typing import Dict

import monai.deploy.core as md
import numpy as np
from monai.deploy.core import ExecutionContext, InputContext, IOType, Operator, OutputContext


@md.input("image", np.ndarray, IOType.IN_MEMORY)
@md.output("image", np.ndarray, IOType.IN_MEMORY)
@md.env(pip_packages=["monai==0.6.0", "numpy"])
class InvertImage(Operator):
    def __init__(self):
        self.logger = logging.getLogger("{}.{}".format(__name__, type(self).__name__))
        super().__init__()

    def compute(self, op_input: InputContext, op_output: OutputContext, context: ExecutionContext):
        arr = op_input.get("image")
        op_output.set(arr[::-1, :, :], "image")
