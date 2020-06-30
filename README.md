# gpusimulation
traffic simulation towards gpu computing.
The CPU and GPU examples are sample.cpp and sample_gpu.cpp.

## To compile
```
make
```

## Data preprocess
```
python3 data/data_process.py
```

## To run CPU
```
sample $INPUT_DATA $OUTPUT_FILE
```

## To run single GPU
```
sample_multi $INPUT_DATA $OUTPUT_FILE 0
```

## To run multiple GPU
```
sample_multi $INPUT_DATA $OUTPUT_FILE $GPU_IDS
```
For example of running on 4 GPUs:
```
sample_multi data/dataset.json out.json 0 1 2 3
```

The simulation write $OUTPUT_FILE as a json file containing the simulation records. data/data_process.py prepare the input data into a json file for simulation $INPUT_DATA and format the $OUTPUT_FILE into the needed json file.

## rm
```
rm sample sample_single sample_multi Model.o
```