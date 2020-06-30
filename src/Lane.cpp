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
    int new_sig = (t%signals[2]) >=signals[0] && (t%signals[2]) <= signals[1];
    bool change = new_sig==0 && can_pass==1;
    can_pass=new_sig;
    return change;
}

    void Lane::count_cool_down(){
        if(cool_down>0)
            cool_down--;
    }
    void Lane::reset_cool_down(){
        cool_down=ht;
    }
