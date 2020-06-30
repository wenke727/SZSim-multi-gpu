#ifndef MODEL_HPP
#define MODEL_HPP
#include "Road.hpp"
#include <string>


class Model
{
public:
    int n_road;  //To be set to any values.
    int n_lane;  //To be set to any values.
    int dt;    //time step size.
    int t_end; //end time.

    float car_length;
    float car_distance;
    float car_actual_length;

    float v_max_global; //in unit of m/s
    float v_min_global;

    std::vector<Road*> roads;
    std::vector<Lane*> lanes;

    //All the parameters for all roads in GPU computing. The parameters are precalculated once before the simulation.
    float *v_max;          // Max speed in unit of m/s
    float *v_min;          // Min speed in unit of m/s
    float *a;              // Alpha for speed calculation
    float *b;              // Beta for speed calculation
    float density_jam;    //Jam density. This can be precalculated
    float *density_factor; // This can be precalculated by = 1.0/((number_lane_per_road[i] * length[i])/1000)

    float* temp_per_lane;
    float* temp_per_road;

    //Status for all roads. They are computed in each time step.

    float* density; //Density of the road.
    float* speed;   //Speed of the road, based on density.
    float* n_running;

    Model(std::string filename, float dt, float t_end, float car_length, float car_distance,float v_max_global, float v_min_global);
    //void initialize_roads();
    void initialize_memories();

    //Calculate the speed for all roads
    void get_speed();
    //Update the location of all vehicles on all roads with calculated speed
    void update_location();

    void enqueue_vehicles(Lane *lane, int t);

    void release_vehicles(Lane *lane, int t);

    void load_input_vehicles(Road *road, int t);
    void release_from_park(Lane *lane, int t);

    void step(int t);

    void loop();

    void output_stats(std::string output_file);
};

#endif
