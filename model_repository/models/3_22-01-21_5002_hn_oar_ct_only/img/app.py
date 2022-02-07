from monai.deploy.core import Application

from ops.op_invert import InvertImage
from ops.op_reader import DataLoader
from ops.op_writer import SegmentationWriter
from ops.op_crop_img_and_mask import CropImage
from ops.op_inference import PredictImage
from ops.op_restore_dimensions import RestoreImageDimensions
from ops.op_up_scale import UpscaleImage

class PCMInteractive(Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compose(self):
        # Creates the DAG by link the operators
        # 0 Dataloader
        dataloader_op = DataLoader()
        # 1 Invert
        inverter_op = InvertImage()

        # 3 Crop
        crop_op = CropImage()

        # 4 Predict
        predict_op = PredictImage()

        # 5 Uncrop
        restore_dim_op = RestoreImageDimensions()

        # 6 Upscale
        scale_up_op = UpscaleImage()

        inverter_op1 = InvertImage()

        writer_op = SegmentationWriter()

        # Flows
        self.add_flow(dataloader_op, inverter_op, {"image": "image"})

        self.add_flow(inverter_op, crop_op, {"image": "image"})

        self.add_flow(dataloader_op, predict_op, {"ref_image": "ref_image"})
        self.add_flow(crop_op, predict_op, {"image": "image"})

        self.add_flow(predict_op, restore_dim_op, {"seg": "seg"})
        self.add_flow(dataloader_op, restore_dim_op, {"ref_image": "ref_image"})
        self.add_flow(crop_op, restore_dim_op, {"bounding_box": "bounding_box"})

        self.add_flow(restore_dim_op, scale_up_op, {"seg": "seg"})

        self.add_flow(scale_up_op, inverter_op1,  {"seg": "image"})

        self.add_flow(inverter_op1, writer_op, {"image": "seg"})
        self.add_flow(dataloader_op, writer_op, {"ref_image": "ref_image"})

if __name__ == "__main__":
    # Creates the app and test it standalone. When running is this mode, please note the following:
    #     -i <DICOM folder>, for input DICOM CT series folder
    #     -o <output folder>, for the output folder, default $PWD/output
    #     -m <model file>, for model file path
    # e.g.
    #     python3 app.py -i input -m model.ts
    #
    PCMInteractive(do_run=True)

