#include "Model.hpp"
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <chrono>
#include "../nlohmann/json.hpp"

using json = nlohmann::json;

bool vehicle_comp(const Vehicle* first, const Vehicle* second){
	return first->time < second->time;
}


void initialize_roads(Model* model, json j)
{
    int lane_index = 0;
    for (json::iterator it = j.begin(); it != j.end(); ++it)
    {
        int index = (*it)["index"].get<int>();
        float length = (*it)["length"].get<float>();
        float a = (*it)["a"].get<float>();
        float b = (*it)["b"].get<float>();
        Road *road = new Road(index, length, a, b);
        model->roads.push_back(road);
        int index_in_road=0;
        for (json::iterator it_lane = (*it)["lanes"].begin(); it_lane != (*it)["lanes"].end(); ++it_lane)
        {
            Lane *lane = new Lane(lane_index++, index_in_road++, length, index, (int)(length / model->car_actual_length), (*it_lane)["direction"].get<int>(),(*it_lane)["ht"].get<int>());
            for (json::iterator it_s = (*it_lane)["signals"].begin(); it_s != (*it_lane)["signals"].end(); ++it_s)
                lane->signals.push_back((*it_s).get<int>());
            model->lanes.push_back(lane);
            road->lanes.push_back(lane);
        }
        road->organize_lanes_in_directrion();
        int v_index = 0;
        for (json::iterator it_v = (*it)["vehicles"].begin(); it_v != (*it)["vehicles"].end(); ++it_v)
        {
            Vehicle *v = new Vehicle((*it_v)["time"].get<int>());
            v->index = v_index++;
            for (json::iterator it_r = (*it_v)["roads"].begin(); it_r != (*it_v)["roads"].end(); ++it_r)
                v->roads.push_back((*it_r).get<int>());
            for (json::iterator it_d = (*it_v)["directions"].begin(); it_d != (*it_v)["directions"].end(); ++it_d)
                v->directions.push_back((*it_d).get<int>());
            road->vehicles_to_load.push_back(v);
        }
        road->vehicles_to_load.sort(vehicle_comp);
        road->vehicle_load_itr=road->vehicles_to_load.begin();

    }
    model->n_road = model->roads.size();
    model->n_lane = model->lanes.size();
}

Model::Model(std::string filename, float dt, float t_end, float car_length, float car_distance, float v_max_global, float v_min_global) : dt(dt), t_end(t_end), car_length(car_length), car_distance(car_distance), v_max_global(v_max_global), v_min_global(v_min_global)
{
    car_actual_length = car_length + car_distance;
    std::ifstream i(filename);
    json j;
    i >> j;
    initialize_roads(this, j);
    initialize_memories();
}
void Model::initialize_memories()
{
    v_max = (float *)malloc(n_road * sizeof(float));
    v_min = (float *)malloc(n_road * sizeof(float));
    a = (float *)malloc(n_road * sizeof(float));
    b = (float *)malloc(n_road * sizeof(float));

    density_jam = 1000 / (car_actual_length);
    density_factor = (float *)malloc(n_road * sizeof(float));

    density = (float *)malloc(n_road * sizeof(float));
    speed = (float *)malloc(n_road * sizeof(float));
    n_running = (float *)malloc(n_road * sizeof(float));
    for (int i = 0; i < n_road; i++)
    {
        v_max[i] = v_max_global;
        v_min[i] = v_min_global;
        a[i] = roads[i]->a;
        b[i] = roads[i]->b;
        density_factor[i] = 1.0 / ((roads[i]->lanes.size() * roads[i]->length) / 1000);
        n_running[i] = 0;
    }

    temp_per_road = (float *)malloc(n_road * sizeof(float));
    temp_per_lane = (float *)malloc(n_lane * sizeof(float));
}


//Calculate the speed for all roads
void Model::get_speed()
{
#pragma parallel for
    for (int i = 0; i < n_road; i++)
    {
        density[i] = n_running[i] * density_factor[i];
    }

#pragma parallel for
    for (int i = 0; i < n_road; i++)
    {
        speed[i] = v_min[i] + (v_max[i] - v_min[i]) * pow(1 - pow(density[i] / density_jam, a[i]), b[i]);
    }
}

//Update the location of all vehicles on all roads with calculated speed
void Model::update_location()
{
//CPU Parallel
#pragma parallel for
    for (int i = 0; i < n_road; i++)
    {
        for (int j = 0; j < roads[i]->lanes.size(); j++)
        {
            for (int k = 0; k < roads[i]->lanes[j]->vehicles.size(); k++)
            {
                roads[i]->lanes[j]->vehicles[k]->location += speed[i] * dt;
            }
        }
    }
}

void Model::enqueue_vehicles(Lane *lane, int t)
{
    while (!lane->vehicles.empty() && lane->vehicles.front()->location >= lane->length)
    {
        Vehicle *v = lane->vehicles.front();
        v->location = 0;
        lane->queue.push_back(v);
        lane->vehicles.erase(lane->vehicles.begin());
        lane->running--;
        lane->n_queue++;
        v->enqueue(t);
    }
}

void Model::release_vehicles(Lane *lane, int t)
{
    if (lane->cool_down==0 && lane->can_pass && !lane->queue.empty())
    {
        Vehicle *v = lane->queue.front();
        if (v->roadIndex == v->roads.size())
        {
            lane->pop_queue_front();
            lane->reset_cool_down();
            v->finish(t);
        }
        else
        {
            std::vector<Lane *> lanes = roads[v->roads[v->roadIndex]]->lanes_per_direction[v->directions.front()];
            Lane *min_lane = nullptr;
            int min = 99999;
            for (int i = 0; i < lanes.size(); i++)
            {
                if (lanes[i]->capacity > 0 && lanes[i]->n_queue < min)
                {
                    min = lanes[i]->n_queue;
                    min_lane = lanes[i];
                }
            }
            if (min_lane != nullptr)
            {
                min_lane->push(v);
                v->finish(t);
                v->start_road(t, min_lane->index_in_road);
                lane->pop_queue_front();
                lane->reset_cool_down();
            }
        }
    }
}

void Model::load_input_vehicles(Road *road, int t)
{
    while (road->vehicle_load_itr != road->vehicles_to_load.end() && (*(road->vehicle_load_itr))->time == t)
    {
        Vehicle *v = *(road->vehicle_load_itr);
        road->vehicle_load_itr++;
        std::vector<Lane *> lanes = road->lanes_per_direction[v->directions.front()];
        
        Lane *min_lane = nullptr;
        int min = 99999;
        for (int i = 0; i < lanes.size(); i++)
        {
            if (lanes[i]->capacity > 0 && lanes[i]->n_queue < min)
            {
                min = lanes[i]->n_queue;
                min_lane = lanes[i];
            }
        }
        //Either push to lane or park
        if (min_lane != nullptr)
        {
            min_lane->push(v);
            v->start_road(t, min_lane->index_in_road);
        }
        else
        {
            min_lane = lanes[0];
            min = lanes[0]->n_queue;
            for (int i = 1; i < lanes.size(); i++)
            {
                if (lanes[i]->n_queue < min)
                {
                    min = lanes[i]->n_queue;
                    min_lane = lanes[i];
                }
                min_lane->parks.push_back(v);
            }
        }
    }
}

void Model::release_from_park(Lane *lane, int t)
{
    while (lane->capacity>0 && !lane->parks.empty())
    {
        Vehicle *v = lane->queue.front();
        
        lane->push(v);
        v->start_road(t, lane->index_in_road);
        lane->parks.pop_front();
    }
}

void Model::step(int t)
{
#pragma parallel for
    for (int i = 0; i < n_road; i++){
        load_input_vehicles(roads[i], t);
    }

#pragma parallel for
    for (int i = 0; i < n_lane; i++)
    {
        bool change_to_red = lanes[i]->set_signal(t);
        if(change_to_red){
            for(auto v_itr=lanes[i]->queue.begin(); v_itr!=lanes[i]->queue.end(); v_itr++)
                (*v_itr)->enqueue(t);
        }
        lanes[i]->count_cool_down();
        temp_per_lane[i] = 0;
        enqueue_vehicles(lanes[i], t);
        release_from_park(lanes[i], t);
    }


#pragma parallel for
    for (int i = 0; i < n_lane; i++)
    {
        release_vehicles((lanes[i]), t);
    }

    memset(n_running, 0, n_road*sizeof(float));

#pragma parallel for
    for (int i = 0; i < n_lane; i++){
        n_running[lanes[i]->road_index]+=lanes[i]->running;
    }
    //Simulation of Roads
    get_speed();
    update_location();
}

void Model::loop()
{
    std::chrono::steady_clock::time_point begin = std::chrono::steady_clock::now(); 
    for (int t = 0; t < t_end; t += dt)
    {
        step(t);
    }
    std::chrono::steady_clock::time_point end = std::chrono::steady_clock::now();  
    std::cout << "Time difference = " << std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count() << "[µs]" << std::endl;
    // std::cout << "Time difference = " << std::chrono::duration_cast<std::chrono::seconds>(end - begin).count() << "[s]" << std::endl;

    return;

}

void Model::output_stats(std::string outputfile){
    json total;
    for (int i = 0; i < n_road; i++)
    {
        for (auto j = roads[i]->vehicles_to_load.begin(); j != roads[i]->vehicles_to_load.end(); j++)
        {
            Vehicle* vehicle = *j;
            for(int k = 0; k < vehicle->stats.size(); k++){
                json record;
                record["start_road"]=i;
                record["vehicle"]=vehicle->index;
                record["road"]=vehicle->roads[k];
                record["lane"]=vehicle->stats[k].lane;
                record["start_time"] = vehicle->stats[k].start_time;
                record["end_time"] = vehicle->stats[k].end_time;
                record["queue_time"] = vehicle->stats[k].end_time-vehicle->stats[k].queue_time;
                record["queue_number"] = vehicle->stats[k].queue_number;
                total.push_back(record);
            }
        }
    }
    std::ofstream o(outputfile);
    o << std::setw(4) << total << std::endl;
}
