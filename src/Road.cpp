#include "Road.hpp"
Road::Road(int index, float length, float a, float b) : index(index), length(length), a(a), b(b)
{
    for(int i = 0; i < 3; i++)
        lanes_per_direction[i] = std::vector<Lane*>();
}

void Road::organize_lanes_in_directrion(){
    for(int i = 0; i < lanes.size(); i++){
        switch(lanes[i]->direction){
            case LEFT:
                lanes_per_direction[LEFT].push_back(lanes[i]);
                break;
            case RIGHT:
                lanes_per_direction[RIGHT].push_back(lanes[i]);
                break;
            case FRONT:
                lanes_per_direction[FRONT].push_back(lanes[i]);
                break;
            case LEFT_FRONT:
                lanes_per_direction[LEFT].push_back(lanes[i]);
                lanes_per_direction[FRONT].push_back(lanes[i]);
                break;                   
            case RIGHT_FRONT:
                lanes_per_direction[RIGHT].push_back(lanes[i]);
                lanes_per_direction[FRONT].push_back(lanes[i]);
                break;         
            case LEFT_RIGHT:
                lanes_per_direction[RIGHT].push_back(lanes[i]);
                lanes_per_direction[LEFT].push_back(lanes[i]);
                break;    
            case ALL:
                lanes_per_direction[RIGHT].push_back(lanes[i]);
                lanes_per_direction[LEFT].push_back(lanes[i]);
                lanes_per_direction[FRONT].push_back(lanes[i]);
                break;    
        }
    }
}