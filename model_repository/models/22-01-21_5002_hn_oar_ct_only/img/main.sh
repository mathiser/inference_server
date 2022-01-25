#!/bin/bash

nnUNet_predict -i $INPUT -o $OUTPUT -t 5002
rsync -av --exclude '*.nii.gz' $INPUT/ -o $OUTPUT/