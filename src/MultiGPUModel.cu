#include "MultiGPUModel.hpp"
#include "GPUModel.hpp"
//#include <helper_functions.h>
//#include <helper_cuda.h>
#include <cuda_runtime.h>

MultiGPUModel::MultiGPUModel(std::string filename, float dt, float t_end, float car_length, float car_distance, float v_max_global, float v_min_global, std::vector<int> gpu_ids)
    : Model(filename, dt, t_end, car_length, car_distance, v_max_global, v_min_global)
{
    this->gpu_ids = gpu_ids;
    int n_road_gpu = n_road / gpu_ids.size();
    for (int i = 0; i < gpu_ids.size() - 1; i++)
    {
        n_road_per_gpu.push_back(n_road_gpu);
    }
    n_road_per_gpu.push_back(n_road - n_road_gpu * (gpu_ids.size() - 1));
    initialize_gpu_memory();
}

void MultiGPUModel::initialize_gpu_memory()
{
    int padding = 0;
    for (int i = 0; i < gpu_ids.size(); i++)
    {
        cudaSetDevice(gpu_ids[i]);
        cudaStream_t stream;
        cudaStreamCreate(&stream);
        streams.push_back(stream);
        density_gpu.push_back(0);
        speed_gpu.push_back(0);
        n_running_gpu.push_back(0);
        density_factor_gpu.push_back(0);
        v_min_gpu.push_back(0);
        v_max_gpu.push_back(0);
        a_gpu.push_back(0);
        b_gpu.push_back(0);

        cudaError_t error;
        error = cudaMalloc((void **)&(density_gpu[i]), n_road_per_gpu[i] * sizeof(float));
        if (error != cudaSuccess)
        {
            printf("cudaMalloc density_gpu returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
            exit(EXIT_FAILURE);
        }
        error = cudaMalloc((void **)&(speed_gpu[i]), n_road_per_gpu[i] * sizeof(float));
        if (error != cudaSuccess)
        {
            printf("cudaMalloc speed_gpu returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
            exit(EXIT_FAILURE);
        }
        error = cudaMalloc((void **)&(n_running_gpu[i]), n_road_per_gpu[i] * sizeof(float));
        if (error != cudaSuccess)
        {
            printf("cudaMalloc n_running_gpu returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
            exit(EXIT_FAILURE);
        }
        error = cudaMalloc((void **)&(density_factor_gpu[i]), n_road_per_gpu[i] * sizeof(float));
        if (error != cudaSuccess)
        {
            printf("cudaMalloc density_factor_gpu returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
            exit(EXIT_FAILURE);
        }
        error = cudaMalloc((void **)&(v_min_gpu[i]), n_road_per_gpu[i] * sizeof(float));
        if (error != cudaSuccess)
        {
            printf("cudaMalloc v_min_gpu returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
            exit(EXIT_FAILURE);
        }
        error = cudaMalloc((void **)&(v_max_gpu[i]), n_road_per_gpu[i] * sizeof(float));
        if (error != cudaSuccess)
        {
            printf("cudaMalloc v_max_gpu returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
            exit(EXIT_FAILURE);
        }
        error = cudaMalloc((void **)&(a_gpu[i]), n_road_per_gpu[i] * sizeof(float));
        if (error != cudaSuccess)
        {
            printf("cudaMalloc a_gpu returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
            exit(EXIT_FAILURE);
        }
        error = cudaMalloc((void **)&(b_gpu[i]), n_road_per_gpu[i] * sizeof(float));
        if (error != cudaSuccess)
        {
            printf("cudaMalloc b_gpu returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
            exit(EXIT_FAILURE);
        }
        error = cudaMemcpy(density_factor_gpu[i], density_factor + padding, n_road_per_gpu[i] * sizeof(float), cudaMemcpyHostToDevice);
        if (error != cudaSuccess)
        {
            printf("cudaMemcpy(density_factor_gpu, density_factor) returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
            exit(EXIT_FAILURE);
        }

        error = cudaMemcpy(v_min_gpu[i], v_min + padding, n_road_per_gpu[i] * sizeof(float), cudaMemcpyHostToDevice);
        if (error != cudaSuccess)
        {
            printf("cudaMemcpy(v_min_gpu, v_min) returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
            exit(EXIT_FAILURE);
        }

        error = cudaMemcpy(v_max_gpu[i], v_max + padding, n_road_per_gpu[i] * sizeof(float), cudaMemcpyHostToDevice);
        if (error != cudaSuccess)
        {
            printf("cudaMemcpy(v_max_gpu, v_max) returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
            exit(EXIT_FAILURE);
        }

        error = cudaMemcpy(a_gpu[i], a + padding, n_road_per_gpu[i] * sizeof(float), cudaMemcpyHostToDevice);
        if (error != cudaSuccess)
        {
            printf("cudaMemcpy(a_gpu, a) returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
            exit(EXIT_FAILURE);
        }
        error = cudaMemcpy(b_gpu[i], b + padding, n_road_per_gpu[i] * sizeof(float), cudaMemcpyHostToDevice);
        if (error != cudaSuccess)
        {
            printf("cudaMemcpy(b_gpu, b) returned error %s (code %d), line(%d)\n", cudaGetErrorString(error), error, __LINE__);
            exit(EXIT_FAILURE);
        }

        padding += n_road_per_gpu[i];
    }
}

//Calculate the density for all roads
void MultiGPUModel::get_speed()
{
    unsigned thread = 128;
    int padding = 0;
    for (int i = 0; i < gpu_ids.size(); i++)
    {
        unsigned block = ceil(1.0f * n_road_per_gpu[i] / thread);
        cudaSetDevice(gpu_ids[i]);
        cudaMemcpyAsync(n_running_gpu[i], n_running + padding, n_road_per_gpu[i] * sizeof(float), cudaMemcpyHostToDevice, streams[i]);

        speed_kernel<<<block, thread, 0, streams[i]>>>(speed_gpu[i], n_running_gpu[i], density_factor_gpu[i], v_min_gpu[i], v_max_gpu[i], a_gpu[i], b_gpu[i], n_road_per_gpu[i], density_jam);
        cudaMemcpyAsync(speed + padding, speed_gpu[i], n_road_per_gpu[i] * sizeof(float), cudaMemcpyDeviceToHost, streams[i]);
        padding += n_road_per_gpu[i];
    }
    cudaDeviceSynchronize();
}
