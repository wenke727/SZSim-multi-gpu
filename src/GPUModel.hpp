#ifndef GPUMODEL_HPP
#define GPUMODEL_HPP
#include "Model.hpp"
#include <thrust/device_vector.h>
#include <vector>

__global__ void speed_kernel(float* speed_gpu, float* n_running_gpu, float* density_factor_gpu, float* v_min_gpu, float* v_max_gpu, float* a_gpu, float* b_gpu, int n_road, float density_jam);

class GPUModel : public Model{
public:

    float* density_gpu; //Density of the road.
    float* speed_gpu;   //Speed of the road, based on density.
    float* n_running_gpu;
    float* density_factor_gpu;
    float* v_min_gpu;
    float* v_max_gpu;    
    float* a_gpu;
    float* b_gpu;


    GPUModel(std::string filename, float dt, float t_end, float car_length, float car_distance,float v_max_global, float v_min_global);
    void initialize_gpu_memory();


    void get_speed();
};

#endif
