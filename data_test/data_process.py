#coding=utf-8
import pandas as pd
import numpy as np
import datetime
import copy
import random
import math
import csv
import os 



def signal_start(signal):
    return signal[0]

ENCODING_ = 'utf-8'
SPLIT = '*'

##
car_len = 5  ##
hs = 0.6     ##
jam_density=1000/(car_len+hs)  ##
free_speed=60  ##

##

stime = datetime.datetime(1900, 1, 1, 17, 0, 0)  ##
etime= datetime.datetime(1900, 1, 1, 21, 0, 0)   ##
prestime=stime-datetime.timedelta(minutes=0)    ##


tripdata_path = os.path.join( os.path.dirname(__file__), 'trip_data_100_trips.csv')
roaddata_path = os.path.join( os.path.dirname(__file__), 'road_data.csv')
signaldata_path = os.path.join( os.path.dirname(__file__), 'signal_data.csv')
outputdata_path = os.path.join( os.path.dirname(__file__), 'dataset.json')

roadname_list = list( pd.read_csv(roaddata_path, encoding=ENCODING_)['FNODE&TNODE'].astype(str).unique())
ab=[[1,1] for x in range(len(roadname_list))]  ##


##
def comom_num(a,b):
    lala=0
    zifu=''
    pipi=0
    for i in range(len(a)):
        for j in range(len(b)):
            if a[i]==b[j]:
                zifu+=a[i]
    for i in range(len(zifu)):
        if zifu[i]=='右':
            lala+=1
        elif zifu[i]=='左':
            lala += 1
        elif zifu[i]=='直':
            lala += 1
    for i in range(len(a)):
        if a[i]=='右':
            pipi+=1
        elif a[i]=='左':
            pipi += 1
        elif a[i]=='直':
            pipi += 1
    return lala,zifu,pipi   ##

##
def get_roaddata(roadname,roaddata):
    one=[]
    for i in range(len(roaddata)):
        if roadname==roaddata[i][2]:
            one.append(roaddata[i])
    for i in range(len(one)):
        one[i]=list(one[i])
        if one[i][3]=='掉左' or one[i][3]=='掉':
            one[i][3]='左'
        if one[i][3]=='掉直':
            one[i][3]='直左'
    for i in range(len(one)):
        one[i]=list(one[i])
    roaddata = one
    return roaddata

##
def get_tripdata(tripdata_path):  ##
    with open(tripdata_path, encoding = ENCODING_)as csv_file:
        reader = csv.reader(csv_file)
        data = [row[:] for row in reader]
        del data[0]
    for i in range(len(data)):
        if len(data[i][1])>8:
            data[i][1]=data[i][1][:8]   ##
        data[i][1]=datetime.datetime.strptime(data[i][1], r"%H:%M:%S")
        ##
        if SPLIT in data[i][2]:
            data[i][2]=data[i][2].split(SPLIT)
        if SPLIT in data[i][3]:
            data[i][3]=data[i][3].split(SPLIT)
        if isinstance(data[i][2],str)==True:
            data[i][2]=[data[i][2]]
            data[i][3]=[data[i][3]]
        data[i].append(0)  ##
        if len(data[i][2]) != len(data[i][3]):
            print("Error: Vehicle "+str(data[i][0])+" has inequal road and direction")
    return data

##
def get_sigalplan(signaldata_path,prestime,etime):
    with open(signaldata_path, encoding=ENCODING_)as csv_file:
        reader = csv.reader(csv_file)
        data = [row[:] for row in reader]
        del data[0]
    one=data
    for i in range(len(one)):
        one[i][5]=int(one[i][5])
        one[i][6] = int(one[i][6])
        one[i][7] = int(one[i][7])
        one[i].append([])
        st = prestime + datetime.timedelta(seconds=one[i][6])
        et = st + datetime.timedelta(seconds=one[i][5])
        xw = (st - et).seconds  ##
        one[i][8].append(copy.deepcopy([st, et]))
        while et < etime:   ##
            st += datetime.timedelta(seconds=(one[i][7] - one[i][5]))
            et = st + datetime.timedelta(seconds=one[i][5])
            one[i][8].append(copy.deepcopy([st, et]))
        # while one[i][8][0][0] > prestime + datetime.timedelta(seconds=(one[i][7] - one[i][5])):
        #     et = one[i][8][0][0] - datetime.timedelta(seconds=(one[i][7] - one[i][5]))
        #     st = et - datetime.timedelta(seconds=one[i][5])
        #     one[i][8].insert(0, copy.deepcopy([st, et]))
    return one

##
def get_green2(ssa,lane):
    pipi=comom_num(lane,'啦')[2]  ##
    p=[]
    for i in range(len(ssa)):
        p.append(ssa[i][0])
    green_sp = [[prestime, etime]] ##
    if pipi==1:  ##
        for i in range(len(ssa)):
            p = comom_num(lane, ssa[i][0])
            lala = p[0]
            if lala > 0:
                green_sp = copy.deepcopy(ssa[i][1])
    elif pipi>1:
        temp=[]
        for i in range(len(ssa)):
            p = comom_num(lane, ssa[i][0])
            lala = p[0]
            if lala > 0:
                for k in range(len(ssa[i][1])):
                    temp.append(copy.deepcopy(ssa[i][1][k]))
        temp=np.array(list(set([tuple(t) for t in temp])))
        temp=temp.tolist()
        green_sp = temp
    return green_sp

##
def get_road(roadname_list,trip_data,signal_plan,roaddata_path):
    with open(roaddata_path, encoding=ENCODING_)as csv_file:
        reader = csv.reader(csv_file)
        data = [row[:] for row in reader]
        del data[0]
    Road=[v for v in roadname_list]
    for i in range(len(roadname_list)):   ##
        res=get_roaddata(roadname_list[i],data)
        ssa=[]
        right=''  ##
        for j in range(len(signal_plan)):
            if roadname_list[i]==signal_plan[j][3]:
                temp=[]
                temp.append(signal_plan[j][4])  ##
                temp.append(signal_plan[j][8])  ##
                ssa.append(temp)
        for j in range(len(ssa)):
            right+=ssa[j][0]  ##
        lane_leng=res[0][4]
        o_lane=[]
        lr=''  ##
        for j in range(len(res)):
            lr+=res[j][3]
            o_lane.append(res[j][3])
        if '右' in lr and  '右' not in right:
            for j in range(len(o_lane)):
                if '右'in o_lane[j] and len(o_lane[j])==1:
                    o_lane[j]='右转nosig'
        elif '右' not in lr:     ##
            if '右' in right:    ##
                o_lane.append('右')
            else:
                o_lane.append('右转nosig')
        lane=['直'for x in range(len(o_lane))]
        for j in range(len(o_lane)):   ##
            if '左' in o_lane[j]:
                lane[0]= o_lane[j]
            if j>0 and '左' in o_lane[j]:  ##
                lane[1] = o_lane[j]
            if '右' in o_lane[j]:
                lane[-1]= o_lane[j]
        has_R=''
        for j in range(len(lane)):
            has_R+=lane[j]
        if '右' not in has_R:
            lane.append('右转nosig')
        cdz_name=[]
        for j in range(len(lane)):
            if lane[j] not in cdz_name:
                cdz_name.append(lane[j])
        ht=[2 for x in range(len(cdz_name))]
        LANE=[]
        LANE.append(roadname_list[i])  ##
        LANE.append(int(float(lane_leng)))  ##
        LANE.append([])         ##
        LANE.append([])         ##
        LANE.append([1,1])      ##
        LANE.append([0,0])      ##
        t=[]   ##
        x=0
        for j in range(len(lane)):
            temp=[]
            temp.append(lane[j])  ##
            if 'nosig' in lane[j]:  ##
                temp.append(1)
            else:
                temp.append(0)
            temp.append([])           ##
            temp.append([])           ##
            temp.append(copy.copy(lane_leng))  ##
            if 'nosig' in lane[j]:
                temp.append([[prestime,etime]])
            else:
                pass_time = get_green2(ssa,lane[j])
                temp.append(pass_time)  ##
            t.append(temp)
        LANE.append(t)
        LANE.append([cdz_name,ht])
        index = roadname_list.index(LANE[0])
        Road[index] = LANE
    for j in range(len(trip_data)):
        index = roadname_list.index(trip_data[j][2][0])
        Road[index][2].append(trip_data[j])
    return Road

directions_list = ['左', '右', '直','左直','直右', '左右', '左直右'] ##

import json
def vehicleToJson(v):
    time = int((v[1]-stime).total_seconds())
    roads=[]
    if len(v[2]) != len(v[3]):
        print("Error: Vehicle "+str(v[0])+" has inequal road and direction")
    for r in v[2]:
        roads.append(roadname_list.index(r))
    directions = []
    for d in v[3]:
        directions.append(directions_list.index(d))
    return {'index':int(v[0]), 'time':time, 'roads':roads, 'directions':directions}

def laneToJson(lane, ht):
    direction = lane[0]
    if direction=='右转nosig':
        direction='右'
    direction = directions_list.index(direction)
    can_pass = []
    lane[5].sort(key=signal_start)
    for p in lane[5]:
        can_pass.append(int((p[0]-stime).total_seconds()))
        can_pass.append(int((p[1]-stime).total_seconds())+1)
    return {'direction':direction, 'signals':can_pass, 'ht':ht}
def roadToJson(road):
    index = roadname_list.index(road[0])
    length = road[1]
    vehicles = []
    for v in road[2]:
        vehicles.append(vehicleToJson(v))
    a = road[4][0]
    b = road[4][1]
    lanes=[]
    for i in range(len(road[6])):
        lanes.append(laneToJson(road[6][i], 2))
    return {'index': index, 'length': length, 'vehicles': vehicles, 'a':a, 'b':b, 'lanes':lanes}





#程序入口

def pre_process():
    trip_data=get_tripdata(tripdata_path)
    signal_plan = get_sigalplan(signaldata_path,prestime,etime)
    Road = get_road(roadname_list, trip_data, signal_plan,roaddata_path)
    roads = []
    for r in Road:
        roads.append(roadToJson(r))
    f=open(outputdata_path, 'w')
    f.write(json.dumps(roads))

if __name__ =='__main__':
    pre_process()
