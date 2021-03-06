#!/usr/bin/python3
#import cx_Oracle
import pandas as pd
import numpy as np
import datetime
import copy
import random
import math
import csv

#基本设定
car_len = 5  #车身长度
hs = 0.6     #停车间距
jam_density=1000/(car_len+hs)  #阻塞密度
free_speed=60  #畅行速度

# 示例路网所包含有向路段ID
roadname_list=['40014002', '40024001', '40024003', '40034002', '40014004', '40044001', '40024005', '40054002', '40034006', '40064003', '40044005', '40054004', '40064005', '40054006', '40044007', '40074004', '40054008', '40084005', '40064009', '40094006', '40074008', '40084007', '40084009', '40094008']

stime = datetime.datetime(1900, 1, 1, 17, 0, 0)  #开始时间
etime= datetime.datetime(1900, 1, 1, 18, 0, 0)   #结束时间
prestime=stime-datetime.timedelta(minutes=0)    #预热时间
ab=[[1,1] for x in range(len(roadname_list))]  #路段速密函数中的ab值，默认为[1,1]


tripdata_path='data/trip_data.csv'
roaddata_path='data/road_data.csv'
signaldata_path='data/signal_data.csv'

#车辆搜寻目标车道
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
    return lala,zifu,pipi   #ab相同车道组数量/ab相同车道组/a是否混合车道

#获取路段信息
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

#获取需求数据   车辆需求list——[车牌，路径各路口时间，路径各路段集合，各路段车道组集合，距离当前路段停车线距离]
def get_tripdata(tripdata_path):  #车辆路径数据
    with open(tripdata_path)as csv_file:
        reader = csv.reader(csv_file)
        data = [row[:] for row in reader]
        del data[0]
    for i in range(len(data)):
        if len(data[i][1])>8:
            data[i][1]=data[i][1][:8]   #去除毫秒
        data[i][1]=datetime.datetime.strptime(data[i][1], r"%H:%M:%S")
        #以列表组织路径数据
        if '-' in data[i][2]:
            data[i][2]=data[i][2].split('-')
        if '-' in data[i][3]:
            data[i][3]=data[i][3].split('-')
        if isinstance(data[i][2],str)==True:
            data[i][2]=[data[i][2]]
            data[i][3]=[data[i][3]]
        data[i].append(0)  #车辆当前距离停车线距离
    return data

#获取信控方案
def get_sigalplan(signaldata_path,prestime,etime):
    with open(signaldata_path)as csv_file:
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
        xw = (st - et).seconds  #相位绿灯时长  ps：原数据中的GREEN为加上黄灯3s后的有效绿灯时长
        one[i][8].append(copy.deepcopy([st, et]))
        while et < etime:   #该相位绿灯时间段填充
            st += datetime.timedelta(seconds=(one[i][7] - one[i][5]))
            et = st + datetime.timedelta(seconds=one[i][5])
            one[i][8].append(copy.deepcopy([st, et]))
        while one[i][8][0][0] > prestime + datetime.timedelta(seconds=(one[i][7] - one[i][5])):
            et = one[i][8][0][0] - datetime.timedelta(seconds=(one[i][7] - one[i][5]))
            st = et - datetime.timedelta(seconds=one[i][5])
            one[i][8].insert(0, copy.deepcopy([st, et]))
    return one

#给目标车道搜寻可通行绿灯时间
def get_green2(ssa,lane):
    pipi=comom_num(lane,'啦')[2]  #是否混合车道
    p=[]
    for i in range(len(ssa)):
        p.append(ssa[i][0])
    if pipi==1:  #否
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

#获取有向路段list——0路名、1长度、2发车集合、3停车场集合、4速密参数、5拓宽车道长度[w,s]、6车道集合[车道方向，是否放行，行驶集合，路口排队集合，容量剩余，可通行时间]、7[cdz,ht]
def get_road(roadname_list,trip_data,signal_plan,roaddata_path):
    with open(roaddata_path)as csv_file:
        reader = csv.reader(csv_file)
        data = [row[:] for row in reader]
        del data[0]
    Road=[]
    for i in range(len(roadname_list)):   #全实验路段
        res=get_roaddata(roadname_list[i],data)
        ssa=[]
        right=''  #ssa
        for j in range(len(signal_plan)):
            if roadname_list[i]==signal_plan[j][3]:
                temp=[]
                temp.append(signal_plan[j][4])  #转向
                temp.append(signal_plan[j][8])  #绿灯区间
                ssa.append(temp)
        for j in range(len(ssa)):
            right+=ssa[j][0]  #ssa表转向
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
        elif '右' not in lr:     # baslane表中无右转车道
            if '右' in right:    # 有右转信控
                o_lane.append('右')
            else:
                o_lane.append('右转nosig')
        lane=['直'for x in range(len(o_lane))]
        for j in range(len(o_lane)):   #改为左直右标准顺序
            if '左' in o_lane[j]:
                lane[0]= o_lane[j]
            if j>0 and '左' in o_lane[j]:  #多条左转
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
        LANE.append(roadname_list[i])  #路名
        LANE.append(int(lane_leng))  # 车道长度
        LANE.append([])         # 待发车集合
        LANE.append([])         # 停车场集合
        LANE.append([1,1])      # 速密关系式
        LANE.append([0,0])      # 拓宽车道长度和数量，此处均取0
        t=[]   #车道信息集合
        x=0
        for j in range(len(lane)):
            temp=[]
            temp.append(lane[j])  # 转向
            if 'nosig' in lane[j]:  # 0-不放行 1-放行
                temp.append(1)
            else:
                temp.append(0)
            temp.append([])           # 行驶车辆集合
            temp.append([])           # 交叉口排队车辆集合
            temp.append(copy.copy(lane_leng))  # 容量剩余
            if 'nosig' in lane[j]:
                temp.append([[prestime,etime]])
            else:
                pass_time = get_green2(ssa,lane[j])
                temp.append(pass_time)  # 可通行时间
            t.append(temp)
        LANE.append(t)
        for j in range(len(trip_data)):
            if trip_data[j][2][0]==roadname_list[i]:
                LANE[2].append(trip_data[j])
        LANE.append([cdz_name,ht])
        Road.append(LANE)
    return Road

#速度密度函数
def speed(density,X):
    speed = 10.8 + (free_speed- 10.8) * ((1 - (density / jam_density)**X[0])**X[1])
    return speed/3.6

#仿真主程序  评价：需求、延误、瓶颈（溢出）
def simulation(Road,stime,etime):
    print('simulation begin')
    delta_num = 1  # 仿真步长
    delta = datetime.timedelta(seconds=delta_num)
    now=copy.deepcopy(prestime)
    passtime=[[]for x in range(len(Road))]  #为各个路段各车道上次通行的时间，用于判断通行能力
    car_complete=0        #结束行程车辆数
    for i in range(len(Road)):
        for j in range(len(Road[i][6])):
            passtime[i].append(copy.copy(now))
    while now<etime:
        for i in range(len(Road)):  #遍历每个路段
            lane_num=2    #车道数量默认为2
            sum_car=0     #行驶+排队
            pp=[]
            for j in range(len(Road[i][6])):
                sum_car+=len(Road[i][6][j][2])+len(Road[i][6][j][3])
                if Road[i][6][j][0] == '直' or Road[i][6][j][0]== '直右' or Road[i][6][j][0]== '直左' or Road[i][6][j][0] == '左直':
                    pp.append(i)
            len_S=Road[i][5][1]
            road_len=copy.copy(Road[i][1])
            road_cap = (road_len* lane_num-sum_car*(car_len+hs))/(car_len+hs)  #整个路段剩余容量
            lane = []  # 车道名称集合
            car_inroad = 0
            for j in range(len(Road[i][6])):  # 判断路段每个车道组当前是否绿灯
                lane.append(Road[i][6][j][0])
                lane_cap=(road_len-(len(Road[i][6][j][2])+len(Road[i][6][j][3]))*(car_len+hs))/(car_len+hs)  #车道剩余容量
                Road[i][6][j][4]=min(road_cap,lane_cap)     #车道组容量
                car_inroad+=len(Road[i][6][j][2])
                if 'nosig' not in Road[i][6][j][0]:  #无信控则全绿
                    green = 0
                    for k in range(len(Road[i][6][j][5])):  # 遍历各车道可通行时间
                        if Road[i][6][j][5][k][0] <= now <= Road[i][6][j][5][k][-1]:
                            Road[i][6][j][1] = 1
                            green = 1
                    if green == 0:
                        Road[i][6][j][1] = 0
                else:
                    Road[i][6][j][1] = 1
             #待发车发车
            j=0
            while j <len(Road[i][2]):
                if Road[i][2][j][1]<=now:
                    obj_lane=[]
                    for k in range(len(lane)):
                        if comom_num(Road[i][2][j][3][0],lane[k])[0]>0 and Road[i][6][k][4]>0:
                            obj_lane.append(k)  #可选择车道集合
                    if len(obj_lane)==0:        #无容量剩余，转入停车场
                        Road[i][2][j][4] = copy.copy(road_len)  #更新距停车线距离
                        Road[i][3].append(copy.deepcopy(Road[i][2][j]))
                        del Road[i][2][j]
                        j-=1
                    else:      #选择排队较短车道驶入
                        queue=[]
                        for k in range(len(obj_lane)):
                            queue.append(len(Road[i][6][obj_lane[k]][3]))
                        best_lane=obj_lane[queue.index(min(queue))]  #取目标车道中排队最少的
                        Road[i][2][j][4] = copy.copy(road_len)
                        Road[i][6][best_lane][2].append(copy.deepcopy(Road[i][2][j]))
                        del Road[i][2][j]
                        j-=1
                j+=1
            #停车场发车
            j=0
            while j<len(Road[i][3]):
                obj_lane = []
                has_lane=0
                for k in range(len(lane)):
                    if comom_num(Road[i][3][j][3][0], lane[k])[0] > 0:
                        has_lane=1
                        if Road[i][6][k][4] > 0 :
                            obj_lane.append(k)
                if has_lane==0 and Road[i][3][j][3][0]== '左':
                    Road[i][3][j][4] = copy.copy(road_len)
                    Road[i][6][0][2].append(copy.deepcopy(Road[i][3][j]))
                    del Road[i][3][j]
                    j-=1
                if len(obj_lane)>0:
                    queue = []
                    for k in range(len(obj_lane)):
                        queue.append(len(Road[i][6][obj_lane[k]][3]))
                    best_lane = obj_lane[queue.index(min(queue))]
                    Road[i][3][j][4] = copy.copy(road_len)
                    Road[i][6][best_lane][2].append(copy.deepcopy(Road[i][3][j]))
                    del Road[i][3][j]
                    j-=1
                j+=1
            #路段车速更新
            density =car_inroad/ ((lane_num * road_len) / 1000)
            if density >= jam_density:
                density = jam_density
            now_speed = speed(density,Road[i][4])        # 速度更新
            for j in range(len(Road[i][6])):  # 对路段每个车道组
                for k in range(len(Road[i][7][0])):
                    if Road[i][6][j][0]==Road[i][7][0][k]:
                        now_ht=Road[i][7][1][k]
                # 排队车辆放行
                if len(Road[i][6][j][3]) > 0 and Road[i][6][j][1] == 1:
                    if (now - passtime[i][j]).seconds >= now_ht:
                        passtime[i][j]=copy.copy(now)
                        if len(Road[i][6][j][3][0][2]) == 1:  # 此道路为最后一路
                            car_complete+=1
                            del Road[i][6][j][3][0]
                        elif len(Road[i][6][j][3][0][2]) > 1:  # 跳转至下一路段
                            next_fx = Road[i][6][j][3][0][3][1]
                            next_road = Road[i][6][j][3][0][2][1]
                            for l in range(len(Road)):
                                if Road[l][0] == next_road:
                                    lane = []
                                    for n in range(len(Road[l][6])):  # 对路段每个车道组
                                        lane.append(Road[l][6][n][0])
                                    obj_lane = []
                                    find=0
                                    for n in range(len(lane)):
                                        if comom_num(next_fx, lane[n])[0]>0:
                                            find=1
                                            if Road[l][6][n][4] > 0:
                                                obj_lane.append(n)
                                    if len(obj_lane) > 0:
                                        queue = []
                                        for n in range(len(obj_lane)):
                                            queue.append(len(Road[l][6][obj_lane[n]][3]))
                                        best_lane = obj_lane[queue.index(min(queue))]
                                        Road[i][6][j][3][0][4] = copy.copy(Road[l][1])
                                        # print('排队通行==================================================')
                                        del Road[i][6][j][3][0][2][0]
                                        del Road[i][6][j][3][0][3][0]
                                        Road[l][6][best_lane][2].append(copy.deepcopy(Road[i][6][j][3][0]))
                                        del Road[i][6][j][3][0]
                                    else:
                                        if find==0 and next_fx=='左' and next_road[:4]==Road[i][6][j][3][0][2][2][-4:]:  #下一路段无掉头/左转车道
                                            Road[i][6][j][3][0][4] = copy.copy(Road[l][1])
                                            del Road[i][6][j][3][0][2][0]
                                            del Road[i][6][j][3][0][3][0]
                                            Road[l][6][0][2].append(copy.deepcopy(Road[i][6][j][3][0]))
                                            del Road[i][6][j][3][0]
                # 行驶车辆运行
                if len(Road[i][6][j][2])>0:
                    k=0
                    while k <len(Road[i][6][j][2]):
                        Road[i][6][j][2][k][4]=Road[i][6][j][2][k][4]-delta_num*now_speed  #距离停车线距离更新
                        if Road[i][6][j][2][k][4] <= 0 and ((Road[i][6][j][1]== 1 and len(Road[i][6][j][3]) > 0) or Road[i][6][j][1] == 0):
                            Road[i][6][j][3].append(Road[i][6][j][2][k])  # 转入排队集合
                            del Road[i][6][j][2][k]
                            k-=1
                        elif Road[i][6][j][2][k][4] <= 0 and Road[i][6][j][1] == 1 and len(Road[i][6][j][3])==0 :  # 绿灯且无排队车辆
                            if (now - passtime[i][j]).seconds >= now_ht:
                                passtime[i][j] = copy.copy(now)
                                if len(Road[i][6][j][2][k][2]) == 1:  # 此道路为最后一路
                                    del Road[i][6][j][2][k]
                                    k-=1
                                    car_complete+=1
                                else:
                                    next_fx = Road[i][6][j][2][k][3][1]
                                    next_road = Road[i][6][j][2][k][2][1]
                                    for l in range(len(Road)):
                                        if Road[l][0] == next_road:
                                            lane = []
                                            for n in range(len(Road[l][6])):  # 对路段每个车道组
                                                lane.append(Road[l][6][n][0])
                                            obj_lane = []
                                            has_lane=0
                                            for n in range(len(lane)):
                                                if comom_num(next_fx, lane[n])[0] > 0:
                                                    has_lane=1
                                                    if Road[l][6][n][4] > 0:
                                                        obj_lane.append(n)
                                            if len(obj_lane) > 0:
                                                queue = []
                                                for n in range(len(obj_lane)):
                                                    queue.append(len(Road[l][6][obj_lane[n]][3]))
                                                best_lane = obj_lane[queue.index(min(queue))]
                                                Road[i][6][j][2][k][4] = copy.copy(Road[l][1])
                                                Road[i][6][j][2][k][1] = copy.deepcopy(now)
                                                del Road[i][6][j][2][k][2][0]
                                                del Road[i][6][j][2][k][3][0]
                                                Road[l][6][best_lane][2].append(copy.deepcopy(Road[i][6][j][2][k]))
                                                del Road[i][6][j][2][k]
                                                k-=1
                                            else:
                                                if has_lane==1:
                                                    Road[i][6][j][3].append(Road[i][6][j][2][k])  # 转入排队集合
                                                    del Road[i][6][j][2][k]
                                                    k-=1
                                                elif has_lane==0:
                                                    if next_fx == '左' and next_road[:4] == Road[i][6][j][2][0][2][2][-4:]:  # 下一路段无掉头/左转车道
                                                        Road[i][6][j][2][0][4] = copy.copy(Road[l][1])
                                                        del Road[i][6][j][2][0][2][0]
                                                        del Road[i][6][j][2][0][3][0]
                                                        Road[l][6][0][2].append(copy.deepcopy(Road[i][6][j][2][0]))
                                                        del Road[i][6][j][2][0]
                        k+=1
        now+=delta
    car_inpark=0
    car_run=0
    car_queue=0
    for i in range(len(Road)):
        car_inpark+=len(Road[i][3])
        ll=[]
        for j in range(len(Road[i][6])):
            ll.append(Road[i][6][j][0])
        #for j in range(len(Road[i][3])):
            #print('p',Road[i][3][j])
        for j in range(len(Road[i][6])):
            car_run+=len(Road[i][6][j][2])
            car_queue+=len(Road[i][6][j][3])
    S=[car_inpark,car_run,car_queue,car_complete]
    return S

#程序入口
def main():
    trip_data=get_tripdata(tripdata_path)
    signal_plan = get_sigalplan(signaldata_path,prestime,etime)
    Road = get_road(roadname_list, trip_data, signal_plan,roaddata_path)
    now_time = datetime.datetime.now()
    time_cost = [now_time]
    res = simulation(Road, stime, etime)
    time_cost.append(datetime.datetime.now())
    print(res)
    print(time_cost, (time_cost[1] - time_cost[0]).seconds)

if __name__ =='__main__':
    main()
