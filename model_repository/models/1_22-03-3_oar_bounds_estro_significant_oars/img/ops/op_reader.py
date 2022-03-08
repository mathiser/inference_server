import logging
import os.path
from typing import Dict

import SimpleITK as sitk
import monai.deploy.core as md
import numpy as np
from monai.deploy.core import ExecutionContext, DataPath, InputContext, IOType, Operator, OutputContext, Image
from .timer import TimeOP


@md.input("path", DataPath, IOType.DISK)
@md.output("label_array_dict", Dict[str, np.ndarray], IOType.IN_MEMORY)
@md.output("ref_image", sitk.Image, IOType.IN_MEMORY)  ## Original CT

@md.env(pip_packages=["monai==0.6.0", "simpleitk", "numpy"])
class DataLoader(Operator):
    def __init__(self):
        self.logger = logging.getLogger("{}.{}".format(__name__, type(self).__name__))
        super().__init__()

    def compute(self, op_input: InputContext, op_output: OutputContext, context: ExecutionContext):
        ## When merged into oar-label, these values should be used.
        timer = TimeOP(__name__)

        in_path: str = op_input.get("path").path
        ct_img: sitk.Image = self.get_ct_image(in_path)
        ct_img_arr: np.ndarray = sitk.GetArrayFromImage(ct_img)

        op_output.set(ct_img, "ref_image")

        label_array_dict: Dict[str, np.ndarray] = {}
        label_array_dict["tmp_0000.nii.gz"] = ct_img_arr
        label_array_dict["tmp_0001.nii.gz"] = self.get_oar_array(in_path)
        op_output.set(label_array_dict, "label_array_dict")

        print(timer.report())

    def get_array_from_path(self, p: str):
        return sitk.GetArrayFromImage(sitk.ReadImage(p))

    def generate_bounds_array_dict(self, in_path: str) -> Dict[str, np.ndarray]:
        bounds_array_dict = {}
        for f in os.listdir(in_path):
            path = os.path.join(in_path, f)
            bounds_array_dict[f] = self.get_array_from_path(path)
        return bounds_array_dict

    def get_ct_image(self, in_path: str) -> sitk.Image:
        for f in os.listdir(in_path):
            if f == "CT.nii.gz":
                return sitk.ReadImage(os.path.join(in_path, f))
        else:
            raise Exception("No CT found")

    def get_oar_array(self, in_path: str) -> sitk.Image:
        for f in os.listdir(in_path):
            if f == "OAR.nii.gz":
                img = sitk.ReadImage(os.path.join(in_path, f))
                return sitk.GetArrayFromImage(img)
        else:
            raise Exception("No OAR found")
