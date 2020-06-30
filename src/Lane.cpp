#include "Lane.hpp"

Lane::Lane(int index, int index_in_road, float length, int road_index, int max, Direction direction, int ht):index(index), index_in_road(index_in_road), length(length), road_index(road_index), max(max), direction(direction), ht(ht)
{
	total=0;
	running=0;
	capacity=max;
	n_queue=0;
    cool_down=0;
}

void Lane::push(Vehicle *v)
{
    vehicles.push_back(v);
    capacity--;
    total++;
    running++;
}

void Lane::pop_queue_front()
{
    queue.pop_front();
    capacity++;
    total--;
    n_queue--;
}

bool Lane::set_signal(int t){
    if(!signals.empty() && signals.front()==t){
        signals.pop_front();
        //toggle can pass
        can_pass=1-can_pass;
        if(can_pass==0)
            return true;
    }
    return false;
}

    void Lane::count_cool_down(){
        if(cool_down>0)
            cool_down--;
    }
    void Lane::reset_cool_down(){
        cool_down=ht;
    }
