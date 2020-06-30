#coding=utf-8
import pandas as pd
import numpy as np
import datetime
import copy
import random
import math
import csv
import os 

ENCODING_ = 'utf-8'
SPLIT = '*'

##
car_len = 5  ##
hs = 0.6     ##
jam_density=1000/(car_len+hs)  ##
free_speed=60  ##

##

stime = datetime.datetime(1900, 1, 1, 17, 0, 0)  ##
etime= datetime.datetime(1900, 1, 1, 23, 0, 0)   ##
prestime=stime-datetime.timedelta(minutes=0)    ##


tripdata_path = os.path.join( os.path.dirname(__file__), 'trip_data.csv')
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
    return data

##
#获取信控方案
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
    return one

##
def get_green2(ssa,lane):
    pipi=comom_num(lane,'啦')[2] 
    p=[]
    for i in range(len(ssa)):
        p.append(ssa[i])
    green_sp=ssa[0]
    for i in range(len(ssa)):
        p = comom_num(lane, ssa[i][0])
        lala = p[0]
        if lala > 0:
            green_sp = ssa[i]
    return green_sp

##
def get_road(roadname_list,trip_data,signal_plan,roaddata_path):
    with open(roaddata_path)as csv_file:
        reader = csv.reader(csv_file)
        data = [row[:] for row in reader]
        del data[0]
    Road=[]
    for i in range(len(roadname_list)): 
        res=get_roaddata(roadname_list[i],data)
        ssa=[]
        right=''  #ssa
        for j in range(len(signal_plan)):
            if roadname_list[i]==signal_plan[j][3]:

                ssa.append(signal_plan[j])
        for j in range(len(ssa)):
            right+=ssa[j][4] 
        lane_leng=res[0][4]
        o_lane=[]
        lr=''  #sigbaslane
        for j in range(len(res)):
            lr+=res[j][3]
            o_lane.append(res[j][3])
        if '右' in lr and  '右' not in right:
            for j in range(len(o_lane)):
                if '右'in o_lane[j] and len(o_lane[j])==1:
                    o_lane[j]='右转nosig'
        elif '右' not in lr:     
            if '右' in right:    
                o_lane.append('右')
            else:
                o_lane.append('右转nosig')
        lane=['直'for x in range(len(o_lane))]
        for j in range(len(o_lane)): 
            if '左' in o_lane[j]:
                lane[0]= o_lane[j]
            if j>0 and '左' in o_lane[j]: 
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
        ht=[2 for x in range(len(lane))]
        LANE=[]
        LANE.append(roadname_list[i]) 
        LANE.append(int(lane_leng))  
        LANE.append([])        
        LANE.append([])        
        LANE.append([1,1])      
        LANE.append([0,0])      
        t=[]  
        x=0
        for j in range(len(lane)):
            temp=[]
            temp.append(lane[j])  
            if 'nosig' in lane[j]: 
                temp.append(1)
            else:
                temp.append(0)
            temp.append([])           
            temp.append([])         
            temp.append(copy.copy(lane_leng))  
            if 'nosig' in lane[j]:
                temp.append([0,2,2])
            else:
                pass_time = get_green2(ssa,lane[j])
                temp.append([pass_time[6], pass_time[5], pass_time[7]])  
            t.append(temp)
        LANE.append(t)
        for j in range(len(trip_data)):
            if trip_data[j][2][0]==roadname_list[i]:
                LANE[2].append(trip_data[j])
        LANE.append([cdz_name,ht])
        LANE.append(res[0][1])
        Road.append(LANE)
    return Road

directions_list = ['左', '右', '直','左直','直右', '左右', '左直右'] ##

import json
def vehicleToJson(v):
    time = int((v[1]-stime).total_seconds())
    roads=[]
    for r in v[2]:
        roads.append(roadname_list.index(r))
    directions = []
    for d in v[3]:
        directions.append(directions_list.index(d))
    return {'time':time, 'roads':roads, 'directions':directions}

def laneToJson(lane, ht):
    direction = lane[0]
    if direction=='右转nosig':
        direction='右'
    direction = directions_list.index(direction)

    return {'direction':direction, 'signals':lane[5], 'ht':ht}
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
