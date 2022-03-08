import logging
import os.path

import SimpleITK as sitk
import monai.deploy.core as md
import numpy as np
from monai.deploy.core import ExecutionContext, DataPath, InputContext, IOType, Operator, OutputContext


@md.input("", DataPath, IOType.DISK)
@md.output("image", np.ndarray, IOType.IN_MEMORY)
@md.output("ref_image", sitk.Image)
@md.env(pip_packages=["monai==0.6.0", "simpleitk", "numpy"])
class DataLoader(Operator):
    def __init__(self):
        self.logger = logging.getLogger("{}.{}".format(__name__, type(self).__name__))
        super().__init__()

    def compute(self, op_input: InputContext, op_output: OutputContext, context: ExecutionContext):
        in_path = op_input.get().path

        for f in os.listdir(in_path):
            path = os.path.join(in_path, f)
            if "0000" in f:
                img = sitk.ReadImage(path)
                op_output.set(value=sitk.GetArrayFromImage(img), label="image")
                op_output.set(value=img, label="ref_image")
                break

    def get_array_from_path(self, p):
        return sitk.GetArrayFromImage(sitk.ReadImage(p))
