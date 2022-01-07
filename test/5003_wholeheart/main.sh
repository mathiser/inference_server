#!/bin/bash

export INPUT=/input
export OUTPUT=/output
export RESULTS_FOLDER=/model

mkdirs $INPUT $OUTPUT 


nnUNet_predict -i $INPUT -o $OUTPUT -t 5003 -f 0 -m 3d_fullres
