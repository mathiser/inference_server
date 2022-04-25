from monai.deploy.core import Application, resource

from ops.op_down_scale import DownScaleImages
from ops.op_invert import InvertImages
from ops.op_reader import DataLoader
from ops.op_writer import DataWriter
from ops.op_crop_img_and_mask import CropAllImages
from ops.op_inference import Predict
from ops.op_restore_dimensions import RestoreDimensions
from ops.op_up_scale import Upscale
from ops.op_end_invert import EndInvertImages

class ESTROInteractive(Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compose(self):
        ############# OAR pipeline ###############
        dataloader_op = DataLoader()
        writer_op = DataWriter()
        inverter_op = InvertImages()
        downscale_op = DownScaleImages()
        crop_op = CropAllImages(padding=(15, 15, 15))
        predict_op = Predict(nnunet_task=507)
        restore_dim_op = RestoreDimensions()
        scale_up_op = Upscale()
        end_invert_op = EndInvertImages()

        self.add_flow(dataloader_op, inverter_op, {"label_array_dict": "label_array_dict"})
        self.add_flow(inverter_op, downscale_op, {"label_array_dict": "label_array_dict"})
        self.add_flow(dataloader_op, downscale_op, {"ref_image": "ref_image"})
        self.add_flow(downscale_op, crop_op, {"label_array_dict": "label_array_dict"})
        self.add_flow(dataloader_op, predict_op, {"ref_image": "ref_image"})
        self.add_flow(crop_op, predict_op, {"label_array_dict": "label_array_dict"})
        self.add_flow(predict_op, restore_dim_op, {"seg": "seg"})
        self.add_flow(dataloader_op, restore_dim_op, {"ref_image": "ref_image"})
        self.add_flow(crop_op, restore_dim_op, {"bounding_box": "bounding_box"})
        self.add_flow(restore_dim_op, scale_up_op, {"seg": "seg"})
        self.add_flow(downscale_op, scale_up_op, {"scale_factor": "scale_factor"})
        self.add_flow(scale_up_op, end_invert_op,  {"seg": "seg"})
        self.add_flow(dataloader_op, writer_op, {"ref_image": "ref_image"})
        self.add_flow(end_invert_op, writer_op, {"seg": "seg"})
        ######################################

if __name__ == "__main__":
    ESTROInteractive(do_run=True)

