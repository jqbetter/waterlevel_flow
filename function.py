import numpy as np
import pandas as pd
import datetime
import os
import re
import math
from dataloader.draw_function import signal_over_noise_bar
from dataloader.draw_function import draw_radar_install_point
from dataloader.draw_function import draw_section_level_information
from dataloader.draw_function import draw_init,section_velocity_diagram
from dataloader.draw_function import level_q_timing_diagram
from dataloader.utils import data_smoothing,three_significant_figures

dis_dir = "../data/madao/202091-2020123WaterSpeedDis.csv"
level_dir = "../data/madao/实时水位.csv"
flow_dir = "../data/madao/2020818-2020123FlowLevel.csv"
section_dir = "../data/madao/jiemian.csv"


class Radar(object):
    def __init__(self,station_name='',flow_dir = None,dis_dir = None,section_dir = None,manual_dir=None,level_dir=None,radar_local=None):
        super(Radar, self).__init__()
        # self.start = datetime.datetime.now()
        # print("程序开始执行时间 ",self.start)
        draw_init()
        self.datetime_format= ["%Y/%m/%d %H:%M:%S","%Y/%m/%d %H:%M"]
        self.station_name = station_name
        self.root_dir = os.path.split(dis_dir)[0]
        self.doc_dir = os.path.join(self.root_dir,"document/")
        self.fig_dir = os.path.join(self.root_dir, "figure/")
        self.report_dir = os.path.join(self.root_dir,self.station_name+"Program_execution_report.txt")
        if not os.path.exists(self.doc_dir):
            os.mkdir(self.doc_dir)
        if not os.path.exists(self.fig_dir):
            os.mkdir(self.fig_dir)
        self.freport = open(self.report_dir,'w')
        self.freport.write("开始执行时间:"+str(datetime.datetime.now())+"\n")

        self.section_data = pd.read_csv(section_dir, engine="python")
        #self.section_data = self.section_data.values.transpose()
        self.section_dist = self.section_data['起点距'].values
        self.section_high = self.section_data['高程'].values
        if radar_local == None:
            radar_local = 0,self.section_high.max()+1

        draw_radar_install_point(self.section_dist,self.section_high,radar_local,
                                  save_dir=os.path.join(self.fig_dir,self.station_name+"雷达安装位置图.png"))
        #河流最深处，不可取，铜仁最深处为10m，信噪比太低，选用河流中间位置
        # max_deep_local = np.where(self.section_high == np.min(self.section_high))[0][0]
        # self.max_deep = int(self.section_dist[max_deep_local]/10)
        #self.max_deep = int((self.section_dist[-1]/10).__round__(0)//2)
        #print("最深起点距",self.max_deep)
        #print(type(self.max_deep))
        self.len_section = len(self.section_dist)-1

        self.dis_data = pd.read_csv(dis_dir, engine="python")
        self.dis_information,self.max_v_point = self.integrate_sec_data_by_date()
        #print(self.max_v_point)
        if manual_dir != None:
            self.manual_data = pd.read_csv(manual_dir, engine='python')

        if level_dir != None:
            self.level_data = pd.read_csv(level_dir,engine='python')

        elif manual_dir!=None:
            level_datetime = self.manual_data['开始时间'].values
            level_value = self.manual_data['水位'].values
            self.level_data = pd.DataFrame({'时间':level_datetime,'水位':level_value})

        if flow_dir !=None:
            self.flow_data = pd.read_csv(flow_dir,engine="python")
        else:
            if manual_dir!=None:
                self.calculate_q_when_z_unconfidence()

        if os.path.exists(os.path.join(self.doc_dir, self.station_name+"根据分段距离和分段流速计算的流量数据.csv")):
            self.flow_data = pd.read_csv(os.path.join(self.doc_dir, self.station_name+"根据分段距离和分段流速计算的流量数据.csv"),engine="python")

        self.dis_signal_over_noise()
        self.bad_data_list = None
        self.sec_data_filtering()
        #if flow_dir!=None or manual_dir!=None:
        try:
            self.irregular_data_clear()
        except:
            pass

        #self.max_v_point = 0
        #self.flow_data_by_date()
        #print("收集分段流速数据耗费时间",datetime.datetime.now()-self.start)

    def irregular_data_clear(self):
        level = self.flow_data['水位'].values
        flow_ = self.flow_data['流量'].values
        # space = self.flow_data['面积(m2/s)'].values
        velocity = self.flow_data['流速'].values
        # flow_data = self.flow_data.values
        date = self.flow_data['时间'].values
        zero_local1 = np.where(level == 0.0)[0]
        zero_local2 = np.where(flow_ == 0.0)[0]
        zero_local3 = np.where(velocity == 0.0)[0]
        zero_local = np.hstack((zero_local1,zero_local2,zero_local3))
        zero_local = np.unique(zero_local)

        f = open(os.path.join(self.doc_dir, self.station_name+"水位流量为0的时间.txt"), 'w')
        # f.write("时间\n")
        f.close()
        # num_lack_measurement = 0
        with open(os.path.join(self.doc_dir, self.station_name+"水位流量为0的时间.txt"), "a") as f:
            for idx in zero_local:
                str_ = str(date[idx])+"\n"
                f.write(str_)
        zero_local = zero_local.tolist()

        zero_local.sort()
        zero_local.reverse()
        for idx in zero_local:
            self.flow_data = self.flow_data.drop(index=idx)
        print("水位流量数据中共有%d组数据值为0"%len(zero_local))
        self.freport.write("水位流量数据中共有%d组数据值为0\n"%len(zero_local))

    def q_data_filtering(self):#,requirements_dir=None):
        #收集符合标准的数据
        level = self.flow_data['水位'].values
        flow_ = self.flow_data['流量'].values
        # space = self.flow_data['面积(m2/s)'].values
        velocity = self.flow_data['流速'].values
        date = self.flow_data['时间'].values
        #iters = self.flow_data.index

        max_level_date_local = np.where(level == np.max(level))[0][0]
        min_level_date_local = np.where(level == np.min(level))[0][0]
        max_flow_date_local = np.where(flow_ == np.max(flow_))[0][0]
        min_flow_date_local = np.where(flow_ == np.min(flow_))[0][0]
        max_velocity_date_local = np.where(velocity == np.max(velocity))[0][0]
        min_velocity_date_local = np.where(velocity == np.min(velocity))[0][0]

        max_level_date = date[max_level_date_local]
        min_level_date = date[min_level_date_local]
        max_flow_date = date[max_flow_date_local]
        min_flow_date = date[min_flow_date_local]
        max_velocity_date = date[max_velocity_date_local]
        min_velocity_date = date[min_velocity_date_local]

        max_level = level[max_level_date_local]
        min_level = level[min_level_date_local]

        draw_section_level_information(self.section_dist,self.section_high,max_level,min_level,
                                       save_dir=os.path.join(self.fig_dir,self.station_name+"最高水位最低水位图.png"))

        str_max_level = "出现最高水位的时间:"+max_level_date+"水位为%.2fm,流量为%.2fm3/s,流速为%.2fm/s" % (
            max_level,flow_[max_level_date_local],velocity[max_level_date_local])
        str_min_level = "出现最低水位的时间:"+min_level_date+ "水位为%.2fm,流量为%.2fm3/s,流速为%.2fm/s" % (
            min_level,flow_[min_level_date_local],velocity[min_level_date_local])
        str_max_flow = "出现最大流量的时间:" +max_flow_date+ "水位为%.2fm,流量为%.2fm3/s,流速为%.2fm/s" % (
            level[max_flow_date_local],flow_[max_flow_date_local],velocity[max_flow_date_local])
        str_min_flow = "出现最小流量的时间:" +min_flow_date+"水位为%.2fm,流量为%.2fm3/s,流速为%.2fm/s" % (
            level[min_flow_date_local],flow_[min_flow_date_local],velocity[min_flow_date_local])
        str_max_velocity = "出现最大流速的时间:"+max_velocity_date+"水位为%.2fm,流量为%.2fm3/s,流速为%.2fm/s" % (
            level[max_velocity_date_local],flow_[max_velocity_date_local],velocity[max_velocity_date_local])
        str_min_velocity = "出现最小流速的时间:"+ min_velocity_date+ "水位为%.2fm,流量为%.2fm3/s,流速为%.2fm/s" % (
            level[min_velocity_date_local],flow_[min_velocity_date_local],velocity[min_velocity_date_local])

        print(str_max_level)
        print(str_min_level)
        print(str_max_flow)
        print(str_min_flow)
        print(str_max_velocity)
        print(str_min_velocity)

        self.freport.write(str_max_level + '\n')
        self.freport.write(str_min_level + '\n')
        self.freport.write(str_max_flow + '\n')
        self.freport.write(str_min_flow + '\n')
        self.freport.write(str_max_velocity + '\n')
        self.freport.write(str_min_velocity + '\n')
        try:
            o_date = [datetime.datetime.strptime(x, self.datetime_format[0]) for x in date]
        except:
            o_date = [datetime.datetime.strptime(x, self.datetime_format[1]) for x in date]
        o_date = np.array(o_date)
        flag_time = datetime.timedelta(minutes=1.5)
        del_list = []
        for temp_date in self.bad_data_list:
            try:
                temp = datetime.datetime.strptime(temp_date, self.datetime_format[0])
            except:
                temp = datetime.datetime.strptime(temp_date, self.datetime_format[1])

            locals = np.where(abs(o_date-temp)<=flag_time)[0]
            for x in locals:
                del_list.append(x)
        # for idx in iters:
        #     flow_date = datetime.datetime.strptime(date[idx], "%Y-%m-%d %H:%M:%S")
        #     for temp_date in self.bad_data_list:
        #         temp = datetime.datetime.strptime(temp_date, "%Y/%m/%d %H:%M")
        #         delte = temp - flow_date
        #         if delte <= flag_time and delte >= -flag_time:
        #             del_list.append(idx)
        del_list.reverse()
        #print(del_list)
        for idx in del_list:
            level = np.delete(level, idx)
            flow_ = np.delete(flow_, idx)
            # space = np.delete(space, idx)
            velocity = np.delete(velocity, idx)
            date = np.delete(date, idx)

        flow_dict = {"时间": date, "水位": level, "流量": flow_, "流速": velocity}# "面积": space}
        flow_dict = pd.DataFrame(flow_dict)
        #if requirements_dir != None:
        flow_dict.to_csv(os.path.join(self.root_dir,self.station_name+"符合标准的水位流量数据.csv"),index=False,encoding='gb2312')

    def integrate_sec_data_by_date(self):
        #收集整合分段流速,绘制分段流速廓线
        iters = self.dis_data.index
        dis_date = self.dis_data['时间'].values
        dis_distance = self.dis_data['分段距离(m)'].values
        dis_velocity = self.dis_data['流速(m/s)'].values
        dis_confidence = self.dis_data['置信度'].values
        #dis_proportion = self.dis_data['占比'].values
        dis_dict = {}
        sec_vec_dict = {}
        #字典，存储同一时间下的分段流速信息，字典值为列表
        #同一时间的相同分段距离信息存放于一个元组，元组内容依次为分段距离，对应流速，置信度，占比
        for idx in iters:
            dis_tuple = dis_distance[idx],dis_velocity[idx],dis_confidence[idx]#,dis_proportion[idx]
            if not dis_date[idx] in dis_dict.keys():
                dis_dict[dis_date[idx]] = []
            dis_dict[dis_date[idx]].append(dis_tuple)

            dis_str = str(dis_distance[idx])
            if not dis_str in sec_vec_dict.keys():
                sec_vec_dict[dis_str] = []
            sec_vec_dict[dis_str].append(dis_velocity[idx])
        pd.DataFrame(sec_vec_dict).to_csv(os.path.join(self.doc_dir,self.station_name+"各分段对应平均流速.csv"),index=False,encoding='gb2312')
        sec_list = []
        average_velocity = []
        for _,k in enumerate(sec_vec_dict):
            sec_list.append(float(k))
            average_velocity.append(np.mean(sec_vec_dict[k]))
        max_v_point = int(np.where(average_velocity == np.max(average_velocity))[0])
        section_velocity_diagram(sec_list,average_velocity,self.section_dist,self.section_high,
                                 save_dir=os.path.join(self.fig_dir,self.station_name+"分段流速截面图.png"))
        return dis_dict,max_v_point

    def sec_data_filtering(self):
        #根据信噪比筛选数据
        collect_date_str = self.dis_information.keys()
        try:
            collect_date_datetime = [datetime.datetime.strptime(x,self.datetime_format[0]) for x in collect_date_str]
        except:
            collect_date_datetime = [datetime.datetime.strptime(x, self.datetime_format[1]) for x in collect_date_str]

        collect_start_datetime = min(collect_date_datetime)
        collect_end_datetime = max(collect_date_datetime)
        collection_time = collect_end_datetime - collect_start_datetime
        print("开始采集日期与最新采集日期差",collect_start_datetime,collect_end_datetime,collection_time)
        self.freport.write("开始采集日期与最新采集日期差:%s  %s  %s\n"%(str(collect_start_datetime)
                     ,str(collect_end_datetime),str(collection_time)))
        collect_days = collection_time.days + 1
        #collect_seconds = collection_time.seconds
        data_to_be_collected = collect_days * 144  #collect_days*24*6

        #下列代码记录未采集数据的时间，默认间隔为10min
        flag_time = datetime.timedelta(minutes=20)
        date_type = []
        collect_date_str = self.dis_information.keys()
        for idx_datetime in collect_date_str:
            try:
                x = datetime.datetime.strptime(idx_datetime, self.datetime_format[0])
            except:
                x = datetime.datetime.strptime(idx_datetime, self.datetime_format[1])
            date_type.append(x)
        num_data = len(date_type)
        lack_measurement_point = []
        for idx in range(num_data - 2):
            if date_type[idx + 1] - date_type[idx] > flag_time:
                lack_measurement_point.append(idx)

        f = open(os.path.join(self.doc_dir, self.station_name+"缺测数据出现的时间.txt"), 'w')
        f.close()
        with open(os.path.join(self.doc_dir, self.station_name+"缺测数据出现的时间.txt"), "a") as f:
            for idx in lack_measurement_point:
                str_ = "数据缺失时间（开区间):起始时间:" + str(date_type[idx]) + "中止时间:" + str(date_type[idx + 1]) + "\n"
                f.write(str_)

        real_number_data = self.dis_information.keys().__len__()
        print("应采集数据量:", data_to_be_collected)
        print("%d组数据未采集,实际采集数据%d"%(data_to_be_collected-real_number_data,real_number_data))
        #print("实际采集数据%d" % (number_data))
        print("采集比:", real_number_data / data_to_be_collected)

        self.freport.write("应采集数据量:%d\n"%data_to_be_collected)
        self.freport.write("%d组数据未采集,实际采集数据%d\n"%(data_to_be_collected-real_number_data,real_number_data))
        self.freport.write("采集比:%.4f\n"%(real_number_data / data_to_be_collected))

        delete_dir = os.path.join(self.doc_dir,self.station_name+"信噪比低于要求的数据.txt")
        f = open(delete_dir,'w')
        f.close()
        f = open(delete_dir, 'a')
        data_del = []  #待清除的数据
        for k in collect_date_str:
            dis_data = self.dis_information[k]
            #dis_mid = int(len(self.dis_information[k]) / 2)
            if dis_data[self.max_v_point][2] < 0.8:
                #print(k,"数据不符合标准")
                #print(str(10*self.max_deep))
                f.write(k+" 位于%d,信噪比为%.4f\n"%(self.max_v_point*10,dis_data[self.max_v_point][2]))
                data_del.append(k)
        f.close()
        for t in data_del:
            del self.dis_information[t]
        number_data = self.dis_information.keys().__len__()
        print("%d组数据不可用,实际可用数据%d组"%(len(data_del),number_data))
        print("健康数据占比:",number_data/real_number_data)
        self.freport.write("%d组数据不可用,实际可用数据%d组\n"%(len(data_del),number_data))
        self.freport.write("健康数据占比:%.4f\n"%(number_data/real_number_data))
        self.bad_data_list = data_del

    def timing_q_level(self):
        data = pd.read_csv(os.path.join(self.root_dir,self.station_name+"符合标准的水位流量数据.csv"),engine='python')
        fdatetime = data['时间'].values
        fq = data['流量'].values
        flevel = data['水位'].values
        fsq = data_smoothing(fq) #平滑处理后的流量
        data["平滑流量"] = fsq
        level_q_timing_diagram(fdatetime,flevel,fq,fsq,os.path.join(self.fig_dir,self.station_name+"水位流量时序图.png"))
        data.to_csv(os.path.join(self.doc_dir,self.station_name+"时间水位流量平滑流量.csv"),index=False,encoding='gb2312')

    def calculate_q_when_z_unconfidence(self):
        #根据截面，分段流速，水位计算流量
        #若数据库中数据正常，这该函数被使用
        date_time_ = self.level_data['时间'].values
        w_levels = self.level_data['水位'].values
        iters = self.level_data.index
        dis_datetime = self.dis_information.keys()
        flag_time = datetime.timedelta(minutes=5)  # 定位距离目标时间的范围，默认正负5分钟

        keys = [x for x in dis_datetime]
        try:
            dis_time = np.array([datetime.datetime.strptime(k, self.datetime_format[0]) for k in dis_datetime])
        except:
            dis_time = np.array([datetime.datetime.strptime(k, self.datetime_format[1]) for k in dis_datetime])

        # dis_datetime_np = [datetime.datetime.strptime(k,"%Y/%m/%d %H:%M") for k in dis_datetime]
        # dis_datetime_np = np.array(dis_datetime_np)
        save_datetime = []
        save_level = []
        save_flow = []
        save_space = []
        save_v = []

        for idx in iters:
            try:
                collect_time = datetime.datetime.strptime(date_time_[idx],self.datetime_format[0])
            except:
                collect_time = datetime.datetime.strptime(date_time_[idx], self.datetime_format[1])

            collect_level = w_levels[idx]
            water_flow,river_area,water_v = self.calculation_q_by_sec_velocity(collect_time,collect_level,
                                                                               flag_time=flag_time,keys=keys,dis_time=dis_time)

            save_datetime.append(date_time_[idx])
            save_level.append(collect_level)
            save_flow.append(water_flow)
            save_space.append(river_area)
            save_v.append(water_v)

        df = pd.DataFrame({"时间":np.array(save_datetime),
                           "水位":np.array(save_level),
                           '流量':np.array(save_flow),
                           '面积':np.array(save_space),
                           '流速':np.array(save_v)})
        df.to_csv(os.path.join(self.doc_dir,self.station_name+"根据分段距离和分段流速计算的流量数据.csv"),index=False,encoding="gb2312")
        # print("结束时间", datetime.datetime.now())
        # print("总耗费时间", datetime.datetime.now() - self.start)

    def dis_signal_over_noise(self):
        sons = self.dis_data["置信度"].values

        son_num_list = [0,0,0,0,0,0,0,0,0,0]
        for son in sons:
            idx = int(np.ceil(son*10))-1
            #print(idx)
            son_num_list[idx] += 1

        area = np.array([10,20,30,40,50,60,70,80,90,100])
        son_num = np.array(son_num_list)
        son_rate = np.array(100*son_num/np.sum(son_num_list))
        pd.DataFrame({'置信度区间(%)':area,'分布频率(%)':son_rate,'数量':son_num}).to_excel(os.path.join(self.doc_dir, self.station_name+"测扫雷达各分段信噪比.xlsx"),index=False,encoding='gb2312')
        signal_over_noise_bar(son_rate,save_dir=os.path.join(self.fig_dir,self.station_name+"测扫雷达个分段信噪比分布柱状图.png"))

    def calculation_q_by_sec_velocity(self,datetime_str,level,keys=None,flag_time=None,dis_time=None,sec=10.0):
        # 根据截面，分段流速，水位计算流量
        # 若数据库中数据正常，这该函数被使用
        if flag_time == None:
            flag_time = datetime.timedelta(minutes=5)

        if keys == None:
            dis_datetime = self.dis_information.keys()
            keys = [x for x in dis_datetime]
            try:
                dis_time = np.array([datetime.datetime.strptime(k, self.datetime_format[0]) for k in dis_datetime])
            except:
                dis_time = np.array([datetime.datetime.strptime(k, self.datetime_format[0]) for k in dis_datetime])

        high = level - self.section_high
        local_high = np.where(high >= 0)[0]

        idx = np.where(abs(datetime_str - dis_time) < flag_time)[0]

        if len(idx) != 0:
            idx = idx[0]
            dis_data = self.dis_information[keys[idx]]
            water_flows = []
            river_areas = []
            water_v = []
            for i in local_high:
                if i == self.len_section:
                    break
                if i == local_high[-1] and i < self.len_section:
                    local_point = (self.section_dist[i] / sec).__round__(0)
                    local_point = int(local_point) - 1

                    w1 = high[i]
                    h1 = self.section_dist[i + 1] - self.section_dist[i]
                    s = w1 * h1 * 0.125
                    river_areas.append(s)
                    water_f = s * dis_data[local_point][1]
                    water_v.append(dis_data[local_point][1])
                    water_flows.append(abs(water_f))
                    continue

                elif i == local_high[0] and i >= 1:
                    local_point = (self.section_dist[i] / sec).__round__(0)
                    local_point = int(local_point) - 1
                    w1 = high[i]
                    h1 = self.section_dist[i] - self.section_dist[i - 1]
                    s = w1 * h1 * 0.5
                    river_areas.append(s)
                    water_f = s * dis_data[local_point][1]
                    water_v.append(dis_data[local_point][1])
                    water_flows.append(abs(water_f))

                current_distance = (self.section_dist[i + 1] + self.section_dist[i]) / 2
                local_point = (current_distance / sec).__round__(0)

                local_point = int(local_point) - 1
                if local_point >= len(dis_data) - 1:
                    break

                w1 = high[i] + high[i + 1]
                h1 = self.section_dist[i + 1] - self.section_dist[i]
                s = w1 * h1 * 0.5
                river_areas.append(s)
                water_f = s * dis_data[local_point][1]
                water_v.append(dis_data[local_point][1])
                water_flows.append(water_f)

            if len(water_flows) == 0:
                water_flows = [0]
            return np.sum(water_flows), np.sum(river_areas), np.mean(water_v)
        else:
            return 0,0,0

    def comparison_analysis(self):
        epoch = self.manual_data.index
        start_datetime_list = self.manual_data['开始时间'].values
        end_datetime_list = self.manual_data['结束时间'].values
        manual_z = self.manual_data['水位'].values
        manual_q = self.manual_data['流量'].values

        radar_data = pd.read_csv(os.path.join(self.root_dir, self.station_name+"符合标准的水位流量数据.csv"),engine='python')
        radar_z = radar_data['水位'].values
        radar_q = radar_data['流量'].values
        radar_v = radar_data['流速'].values
        #radar_q_after_s = radar_data['平滑流量'].values
        #iters = radar_data.index
        radar_datetime_str_list = radar_data['时间'].values
        radar_datetime_list = []

        for x in radar_datetime_str_list:
            t = datetime.datetime.strptime(x.replace('-','/'), '%Y/%m/%d %H:%M')
            radar_datetime_list.append(t)
        radar_datetime_list = np.array(radar_datetime_list)

        save_date = []
        save_start = []
        save_end = []
        save_z = []
        save_v = []
        save_mq =[]
        save_rq = []
        #save_rsq = []
        f = open(os.path.join(self.doc_dir, self.station_name+"比测试水位差距大的时间和水位.txt"), 'w')
        f.write('    时间     雷达水位 人工水位\n')
        for idx in epoch:
            start_str = start_datetime_list[idx].replace('-','/')
            end_str = end_datetime_list[idx].replace('-','/')

            date_str = re.findall(r"(\d{4}/\d{1,2}/\d{1,2})",start_str)[0]
            time_s = re.findall(r"(\d{1,4}:\d{1,2}[:\d{1,2}])",start_str)[0]
            time_e = re.findall(r"(\d{1,4}:\d{1,2}[:\d{1,2}])",end_str)[0]
            save_date.append(date_str)
            save_start.append(time_s)
            save_end.append(time_e)

            manual_z_flag = manual_z[idx]
            save_z.append(manual_z_flag)
            save_mq.append(manual_q[idx])
            try:
                start_datetime = datetime.datetime.strptime(start_str, self.datetime_format[0])
                end_datetime = datetime.datetime.strptime(end_str, self.datetime_format[0])
            except:
                start_datetime = datetime.datetime.strptime(start_str, self.datetime_format[1])
                end_datetime = datetime.datetime.strptime(end_str, self.datetime_format[1])
            within_time_local = np.where((radar_datetime_list>=start_datetime)&(radar_datetime_list<=end_datetime))[0]

            q_list = []
            v_list = []
            for itr in within_time_local:
                if abs(radar_z[itr]- manual_z_flag) <= 0.02:
                    qt = radar_q[itr]
                else:
                    qt,_,_ = self.calculation_q_by_sec_velocity(radar_datetime_list[itr],manual_z_flag)
                    f.write('%s, %.2f, %.2f\n'%(radar_datetime_str_list[itr],radar_z[itr],manual_z_flag))
                    print(radar_datetime_list[itr], radar_z[itr], manual_z_flag)
                q_list.append(qt)
                v_list.append(radar_v[itr])

            if len(q_list) == 0:
                q_list.append(0)
                if len(v_list) == 0:
                    v_list.append(0)

            save_rq.append(np.mean(q_list))
            save_v.append(np.mean(v_list))
        f.close()
        save_mq = np.array([three_significant_figures(x) for x in save_mq])
        save_rq = np.array([three_significant_figures(x) for x in save_rq])

        pd.DataFrame({"日期":np.array(save_date),
                      "开始时间":np.array(save_start),
                      "停止时间":np.array(save_end),
                      "测时水位":np.array(save_z),
                      "平均流速":np.array(save_v),
                      "实测流量":save_mq,
                      '雷达流量':save_rq}).to_csv(os.path.join(self.doc_dir,self.station_name+'人工雷达数据比测表.csv'),index=False,encoding='gb2312')
                      #'平滑流量':np.array(save_rsq)}).to_csv(os.path.join(self.doc_dir,'人工雷达数据比测表.csv'),index=False,encoding='gb2312')

    def end(self):
        self.freport.write("程序结束时间:"+str(datetime.datetime.now()))
        self.freport.close()



if __name__ == "__main__":
    print("flow run")
    # m = Radar()
    x = [-1,-2,0,9]
    z = np.where(np.array(x)<0)
    print(z)
