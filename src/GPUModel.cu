#include "GPUModel.hpp"
//#include <helper_functions.h>
//#include <helper_cuda.h>
#include <cuda_runtime.h>

__global__ void speed_kernel(float* speed_gpu, float* n_running_gpu, float* density_factor_gpu, float* v_min_gpu, float* v_max_gpu, float* a_gpu, float* b_gpu, int n_road, float density_jam){
	unsigned id = blockIdx.x * blockDim.x + threadIdx.x;
	
	if(id >= n_road)	return;
	
    	speed_gpu[id] = v_min_gpu[id] + (v_max_gpu[id] - v_min_gpu[id]) * powf(1 - powf(n_running_gpu[id] * density_factor_gpu[id] / density_jam, a_gpu[id]), b_gpu[id]);

	return;
}



GPUModel::GPUModel(std::string filename, float dt, float t_end, float car_length, float car_distance,float v_max_global, float v_min_global)
:Model(filename, dt, t_end, car_length, car_distance, v_max_global, v_min_global){
	initialize_gpu_memory();
}


void GPUModel::initialize_gpu_memory(){
    cudaError_t error;
    error = cudaMalloc((void **)&density_gpu, n_road * sizeof(float));
    if (error != cudaSuccess)
    {
        printf("cudaMalloc density_gpu returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
        exit(EXIT_FAILURE);
    }
    error = cudaMalloc((void **)&speed_gpu, n_road * sizeof(float));
    if (error != cudaSuccess)
    {
        printf("cudaMalloc speed_gpu returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
        exit(EXIT_FAILURE);
    }
    error = cudaMalloc((void **)&n_running_gpu, n_road * sizeof(float));
    if (error != cudaSuccess)
    {
        printf("cudaMalloc n_running_gpu returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
        exit(EXIT_FAILURE);
    }
    error = cudaMalloc((void **)&density_factor_gpu, n_road * sizeof(float));
    if (error != cudaSuccess)
    {
        printf("cudaMalloc density_factor_gpu returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
        exit(EXIT_FAILURE);
    }
    error = cudaMalloc((void **)&v_min_gpu, n_road * sizeof(float));
    if (error != cudaSuccess)
    {
        printf("cudaMalloc v_min_gpu returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
        exit(EXIT_FAILURE);
    }
    error = cudaMalloc((void **)&v_max_gpu, n_road * sizeof(float));
    if (error != cudaSuccess)
    {
        printf("cudaMalloc v_max_gpu returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
        exit(EXIT_FAILURE);
    }
    error = cudaMalloc((void **)&a_gpu, n_road * sizeof(float));
    if (error != cudaSuccess)
    {
        printf("cudaMalloc a_gpu returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
        exit(EXIT_FAILURE);
    }
    error = cudaMalloc((void **)&b_gpu, n_road * sizeof(float));
    if (error != cudaSuccess)
    {
        printf("cudaMalloc b_gpu returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
        exit(EXIT_FAILURE);
    }
    error = cudaMemcpy(density_factor_gpu, density_factor, n_road * sizeof(float), cudaMemcpyHostToDevice);
    if (error != cudaSuccess)
    {
        printf("cudaMemcpy(density_factor_gpu, density_factor) returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
        exit(EXIT_FAILURE);
    }

    error = cudaMemcpy(v_min_gpu, v_min, n_road * sizeof(float), cudaMemcpyHostToDevice);
    if (error != cudaSuccess)
    {
        printf("cudaMemcpy(v_min_gpu, v_min) returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
        exit(EXIT_FAILURE);
    }

    error = cudaMemcpy(v_max_gpu, v_max, n_road * sizeof(float), cudaMemcpyHostToDevice);
    if (error != cudaSuccess)
    {
        printf("cudaMemcpy(v_max_gpu, v_max) returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
        exit(EXIT_FAILURE);
    }

    error = cudaMemcpy(a_gpu, a, n_road * sizeof(float), cudaMemcpyHostToDevice);
    if (error != cudaSuccess)
    {
        printf("cudaMemcpy(a_gpu, a) returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
        exit(EXIT_FAILURE);
    }
    error = cudaMemcpy(b_gpu, b, n_road * sizeof(float), cudaMemcpyHostToDevice);
    if (error != cudaSuccess)
    {
        printf("cudaMemcpy(b_gpu, b) returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
        exit(EXIT_FAILURE);
    }
}

//Calculate the density for all roads
void GPUModel::get_speed()
{
    cudaError_t error;
    error = cudaMemcpy(n_running_gpu, n_running, n_road * sizeof(float), cudaMemcpyHostToDevice);

    if (error != cudaSuccess)
    {
        printf("cudaMemcpy(n_running_gpu, n_running) returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
        exit(EXIT_FAILURE);
    }

    unsigned thread = 128;
    unsigned block  = ceil( 1.0f * n_road / thread );
    speed_kernel<<< block, thread >>>(speed_gpu, n_running_gpu, density_factor_gpu, v_min_gpu, v_max_gpu, a_gpu, b_gpu, n_road, density_jam);

    error = cudaMemcpy(speed, speed_gpu, n_road * sizeof(float), cudaMemcpyDeviceToHost);

    if (error != cudaSuccess)
    {
        printf("cudaMemcpy(n_running_gpu, n_running) returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
        exit(EXIT_FAILURE);
    }
}
