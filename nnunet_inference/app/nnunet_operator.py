import logging
import os.path
import os
import monai.deploy.core as md
from monai.deploy.core import ExecutionContext, InputContext, IOType, Operator, OutputContext, DataPath


@md.input("", DataPath, IOType.DISK)
@md.output("", DataPath, IOType.DISK)
@md.env(pip_packages=["monai >= 0.60", "nnunet", "pytorch >= 1.6.0"])
class NnUNetPredictOperater(Operator):
    """ Performs segmentation on .nii.gz files with nnUNet_predict function.
    """

    def __init__(self):
        self.logger = logging.getLogger("{}.{}".format(__name__, type(self).__name__))
        super().__init__()

    def compute(self, op_input: InputContext, op_output: OutputContext, context: ExecutionContext):
        images_folder = op_input.get().path

        if not images_folder:
            raise ValueError("No input folder")
        else:
            print(images_folder)

        output_folder = op_output.get().path
        model_folder = context.models.get()
        print(model_folder.path)
        print(model_folder.name)
        [print(fol, sub) for fol, subs, files in os.walk(model_folder.path) for sub in subs]
        os.environ["RESULTS_FOLDER"] = "/opt/app/models/"
        os.system(f"nnUNet_predict -i {images_folder} -o {output_folder} -f 0 -t 5003")
