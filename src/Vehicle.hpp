#ifndef VEHICLE_HPP
#define VEHICLE_HPP
#include <list>
#include <vector>
#include "Direction.hpp"

class Statistics
{
public:
    int road;
    int lane;
    int start_time=-1;
    int end_time=-1;
    int queue_time=-1;
    int queue_number=0;
};

class Vehicle
{
public:
    int index;
    int time;
    int location = 0;
    std::list<Direction> directions;
    std::vector<int> roads;
    Vehicle(int time) : time(time) {}
    std::vector<Statistics> stats;
    int roadIndex = 0;

    void start_road(int t, int lane_index){
        Statistics stat;
        stat.road = roads[roadIndex++];
        stat.start_time=t;
        stat.lane=lane_index;
        directions.pop_front();
        stats.push_back(stat);
    }

    void enqueue(int t){
        if(stats.front().queue_time==-1)
            stats.front().queue_time=t;
        stats.front().queue_number++;
    }

    void finish(int t){
        stats.front().end_time = t;
        if(t==stats.front().queue_time){
            stats.front().queue_number = 0;
        }
    }
};

#endif
