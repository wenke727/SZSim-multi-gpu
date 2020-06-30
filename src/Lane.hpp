#ifndef LANE_HPP
#define LANE_HPP

#include "Vehicle.hpp"
#include <vector>
class Lane
{
public:
    const int index;
    const float length;
    const int road_index;
    const int index_in_road;
    const int max; //Max number of vehicles
    const Direction direction;
    const int ht;

    std::vector<Vehicle *> vehicles; //Record vehicles locations.
    int capacity;                    // Number of new vehicles allow.
    int total;                       // Number of total vehicles per lane.
    int running;
    int n_queue;
    int cool_down;
    std::list<Vehicle *> queue; //This queue is the ending queue.
    std::list<Vehicle *> parks;

    int can_pass=0;
    std::vector<int> signals;
    Lane(int index, int index_in_road, float length, int road_index, int max, Direction direction, int ht);
    void push(Vehicle *v);
    void pop_queue_front();
    //Return if become red
    bool set_signal(int t);

    void count_cool_down();
    void reset_cool_down();
};

#endif
