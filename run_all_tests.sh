#!/usr/bin/bash
for module in public_api private_api job_consumer;
do
python3 -m unittest discover -s $module
done
