from monai.deploy.core import Application

from ops.op_invert import InvertImages
from ops.op_reader import DataLoader
from ops.op_writer import DataWriter
from ops.op_crop_img_and_mask import CropAllImages
from ops.op_inference import Predict
from ops.op_restore_dimensions import RestoreDimensions
from ops.op_up_scale import Upscale
from ops.op_end_invert import EndInvertImages

class GTVApplication(Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compose(self):
        # Creates the DAG by link the operators
        # 0 Dataloader
        dataloader_op = DataLoader()
        # 1 Invert
        inverter_op = InvertImages()

        # 3 Crop
        crop_op = CropAllImages()

        # 4 Predict
        predict_op = Predict()

        # 5 Uncrop
        restore_dim_op = RestoreDimensions()

        # 6 Upscale
        scale_up_op = Upscale()

        # 7 Invert
        end_invert_op = EndInvertImages()
        writer_op = DataWriter()

        # Flows
        self.add_flow(dataloader_op, inverter_op, {"label_array_dict": "label_array_dict"})

        self.add_flow(inverter_op, crop_op, {"label_array_dict": "label_array_dict"})

        self.add_flow(crop_op, predict_op, {"label_array_dict": "label_array_dict"})
        self.add_flow(dataloader_op, predict_op, {"ref_image": "ref_image"})

        self.add_flow(predict_op, restore_dim_op, {"seg": "seg"})
        self.add_flow(dataloader_op, restore_dim_op, {"ref_image": "ref_image"})
        self.add_flow(crop_op, restore_dim_op, {"bounding_box": "bounding_box"})

        self.add_flow(restore_dim_op, scale_up_op, {"seg": "seg"})

        self.add_flow(scale_up_op, end_invert_op,  {"seg": "seg"})

        self.add_flow(end_invert_op, writer_op, {"seg": "seg"})
        self.add_flow(dataloader_op, writer_op, {"ref_image": "ref_image"})

if __name__ == "__main__":
    # Creates the app and test it standalone. When running is this mode, please note the following:
    #     -i <DICOM folder>, for input DICOM CT series folder
    #     -o <output folder>, for the output folder, default $PWD/output
    #     -m <model file>, for model file path
    # e.g.
    #     python3 app.py -i input -m model.ts
    #
    GTVApplication(do_run=True)

