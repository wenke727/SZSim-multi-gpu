#ifndef MULTIGPUMODEL_HPP
#define MULTIGPUMODEL_HPP
#include "Model.hpp"
#include <thrust/device_vector.h>
#include <vector>


class MultiGPUModel : public Model{
public:

    std::vector<float*> density_gpu; //Density of the road.
    std::vector<float*> speed_gpu;   //Speed of the road, based on density.
    std::vector<float*> n_running_gpu;
    std::vector<float*> density_factor_gpu;
    std::vector<float*> v_min_gpu;
    std::vector<float*> v_max_gpu;    
    std::vector<float*> a_gpu;
    std::vector<float*> b_gpu;

    std::vector<int> n_road_per_gpu;


    std::vector<int> gpu_ids;
    std::vector<cudaStream_t> streams;
    
    MultiGPUModel(std::string filename, float dt, float t_end, float car_length, float car_distance,float v_max_global, float v_min_global, std::vector<int> gpu_ids);
    void initialize_gpu_memory();
    void get_speed();

};

#endif
