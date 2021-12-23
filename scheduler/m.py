import os
from multiprocessing import Pool
import sys

in_fol = sys.argv[1]
out_fol = sys.argv[2]

print(in_fol, out_fol)

def convert_dicom_to_nii(i, o):
    if not os.path.exists(o):
        os.makedirs(o)
    os.system(f"dcm2niix -z y -m y -o {o} {i}")

def get_sub_list(in_fol, out_fol):
    for fol, subs, files in os.walk(in_fol):
        for sub in subs:
            for f in os.listdir(os.path.join(fol, sub)):
                if f.endswith(".dcm"):
                    yield (os.path.join(fol, sub), os.path.join(out_fol, sub))
                    break

if not os.path.exists(out_fol):
    os.makedirs(out_fol)

p = Pool(16)
p.starmap(convert_dicom_to_nii, get_sub_list(in_fol, out_fol))