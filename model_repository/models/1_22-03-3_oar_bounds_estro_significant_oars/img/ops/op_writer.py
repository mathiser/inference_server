import json
import logging
import os.path

import SimpleITK as sitk
import monai.deploy.core as md
import numpy as np
from monai.deploy.core import ExecutionContext, DataPath, InputContext, IOType, Operator, OutputContext

from .timer import TimeOP


@md.input("seg", np.ndarray, IOType.IN_MEMORY)
@md.input("ref_image", sitk.Image, IOType.IN_MEMORY)
@md.output("", DataPath, IOType.DISK)
@md.env(pip_packages=["monai==0.6.0", "simpleitk", "numpy"])
class DataWriter(Operator):
    def __init__(self):
        self.logger = logging.getLogger("{}.{}".format(__name__, type(self).__name__))
        super().__init__()

    def compute(self, op_input: InputContext, op_output: OutputContext, context: ExecutionContext):
        label_dict = {
            "Brainstem": 1,
#            "SpinalCord": 2,
            "Lips": 3,
            "Esophagus": 4,
            "PCM_Low": 5,
            "PCM_Mid": 6,
            "PCM_Up": 7,
            "OralCavity": 8,
            "Submandibular_merged": 9,
            "Thyroid": 10
        }

        timer = TimeOP(__name__)

        out_path = op_output.get().path
        seg = op_input.get("seg")

        img = sitk.GetImageFromArray(seg)
        sitk.WriteImage(img, os.path.join(out_path, "segmentations.nii.gz"))

        with open(os.path.join(out_path, "segmentations.json"), "w") as f:
            f.write(json.dumps(label_dict))
        print(timer.report())

