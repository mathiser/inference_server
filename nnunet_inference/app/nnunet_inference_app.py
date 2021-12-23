from monai.deploy.core import Application, resource
from .nnunet_operator import NnUNetPredictOperater


@resource(cpu=16, gpu=1, memory="16Gi")
class InferenceApp(Application):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # App's name. <class name>('App') if not specified.
        name = "nnunet_inference"
        # App's description. <class docstring> if not specified.
        description = "nnUNet inference app"
        # App's version. <git version tag> or '0.0.0' if not specified.
        version = "0.1.0"

    def compose(self):
        # Creates the model specific segmentation operator
        nnunet_pred_op = NnUNetPredictOperater()

        # Creates the DAG by linking the operators
        self.add_operator(nnunet_pred_op)

if __name__ == "__main__":
    app = InferenceApp(do_run=True)
