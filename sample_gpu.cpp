#include "src/GPUModel.hpp"
#include "src/MultiGPUModel.hpp"
int main(int argc, char **argv)
{
    if (argc < 3)
    {
        printf("Usage: sample DATAFILE OUTPUTFILE\n");
        exit(1);
    }

    std::string filename(argv[1]);
    std::string output_file(argv[2]);
    int dt = 1;
    int t_end = 60 * 60;
    float car_length = 5;
    float car_distance = 0.6;
    float v_max_global = 60.0 / 3.6;
    float v_min_global = 10.8 / 3.6;
    if (argc == 3)
    {
        Model model = GPUModel(filename, dt, t_end, car_length, car_distance, v_max_global, v_min_global);
        model.loop();
        model.output_stats(output_file);
    }
    else
    {
        std::vector<int> gpu_ids;

        for (int i = 3; i < argc; i++)
        {
            gpu_ids.push_back(atoi(argv[i]));
        }
        Model model = MultiGPUModel(filename, dt, t_end, car_length, car_distance, v_max_global, v_min_global, gpu_ids);
        model.loop();
        model.output_stats(output_file);
    }
}
