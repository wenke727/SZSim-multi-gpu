NVCC	  := /usr/local/cuda/bin/nvcc
all: sample sample_single sample_multi

sample_single: sample.cpp src/Lane.cpp src/Road.cpp Model.o
	g++ -std=c++11 -O3 -g sample.cpp src/Lane.cpp src/Road.cpp Model.o -o sample_single

sample: sample.cpp src/Lane.cpp src/Road.cpp Model.o
	g++ -std=c++11 -O3 -g -fopenmp sample.cpp src/Lane.cpp src/Road.cpp Model.o -o sample
sample_multi: sample_gpu.cpp src/Lane.cpp src/Road.cpp src/GPUModel.cu src/MultiGPUModel.cu Model.o
	$(NVCC) -std=c++11 -O3 -g -Xcompiler "-fopenmp" sample_gpu.cpp src/Lane.cpp src/Road.cpp Model.o src/GPUModel.cu src/MultiGPUModel.cu -o sample_multi

Model.o: src/Model.cpp
	g++ -std=c++11 -fopenmp -O3 -g -c src/Model.cpp

clean: 
	rm sample 
	rm sample_single
	rm sample_multi
	rm Model.o

