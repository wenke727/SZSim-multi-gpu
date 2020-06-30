#ifndef ROAD_HPP
#define ROAD_HPP

#include "Lane.hpp"
//Keep all parameters and states of roads on CPU in this class.
class Road
{
public:
    int index;
    float length;
    float a;
    float b;
    std::vector<Lane *> lanes;
    std::list<Vehicle *> vehicles_to_load;
    std::list<Vehicle *>::iterator vehicle_load_itr;

    // Lanes are organized in 3 directions (left, right, front).
    std::vector<Lane *> lanes_per_direction[3];

    Road(int index, float length, float a, float b);

    void organize_lanes_in_directrion();    
};

#endif