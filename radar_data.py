#codeing = utf-8
import numpy as np
import csv
import pandas as pd
import scipy.signal as signal
import random
import os
from dataloader.utils import str_to_date
import matplotlib.pyplot as plt
from fitting import lr_fit
from statsmodels.formula import api

data_dir = "../data/铜仁/backup_2020820-20201126FlowLevel.csv"

class RadarSpeed:
    def __init__(self,data_dir=data_dir,root_dir = "E:\\Test\\data\\"):
        super(RadarSpeed, self).__init__()
        assert os.path.exists(data_dir), "The file does not exist in the data_dir path."
        _, self.file = os.path.split(data_dir)
        self.data = pd.read_csv(data_dir, engine='python')  #原始文件数据，只引用，不改变值
        self.df = self.data                                 # 数据通过文件流传递

        self.root_dir = root_dir
        self.dir = os.path.join(self.root_dir,self.file)
        #self.df.to_csv(self.dir,index=False,encoding="gb2312")

    def speed_dis(self,save_filename="speed_dis_data.csv"):
        keys = ['分段距离(m)', '置信度','流速(m/s)']
        # print(self.df.keys())
        y_dest = self.df[keys[0]].values
        y_v = self.df[keys[2]].values
        ls = np.where(y_dest == 10.)[0]
        step = ls[1] - ls[0]
        v_dis = {}
        keyv = []
        for idx in range(step):
            value = 10.0*(idx+1)
            keyv.append(value)
            v_dis[str(value)] = []

        num_data = len(y_dest)
        for dis in keyv:
            k = str(dis)
            for idx in range(num_data):
                if y_dest[idx] == dis:
                    v_dis[k].append(y_v[idx])

        txt_dir = os.path.join(self.root_dir,"speed_dis_mean.txt")
        with open(txt_dir,"w") :
            pass
        yv = []
        with open(txt_dir,"a") as f:
            for k in keyv:
                mv = np.mean(v_dis[str(k)])
                yv.append(mv)
                f.write(str(k)+":"+str(mv)+"\n")

        vdf = pd.DataFrame(v_dis)
        save_dir = os.path.join(self.root_dir,save_filename)
        vdf.to_csv(save_dir, index=False, encoding="gb2312")

        draw([keyv,yv],"分段流速廓线","分段距离(m)","流速(m/s)")

    def origain_data(self):
        return self.data

    def sort(self,key,ascending=True):
        #按给定键值排序y
        keys = self.df.keys()
        if key in keys:
            self.df = self.df.sort_values(by=key,ascending=ascending)

    def write(self):
        save_dir = os.path.join(self.root_dir,"backup_"+self.file)
        self.df.to_csv(save_dir,index=False,encoding="gb2312")

    def __call__(self):
        return self.df


class RadarLevel:
    def __init__(self,data_dir=data_dir,root_dir = "E:\\Test\\data\\"):
        super(RadarLevel, self).__init__()
        assert os.path.exists(data_dir), "The file does not exist in the data_dir path."
        _, self.file = os.path.split(data_dir)
        self.data = pd.read_csv(data_dir, engine='python')  #原始文件数据，只引用，不改变值
        self.df = self.data                                 # 数据通过文件流传递
        self.keys = ['流量(m3/s)', '面积(m2/s)', '水位(m)', '流速(m/s)', '时间']
        self.root_dir = root_dir
        self.dir = os.path.join(self.root_dir,self.file)
        #self.df.to_csv(self.dir,index=False,encoding="gb2312")

    def origain_data(self):
        return self.data

    def cleansing(self):
        self.df

    def water_level_timing(self, save_filename="water_level_timing.csv"):
        pass

    def water_level_relation(self,save_filename="water_level_relation.txt"):
        # print(self.df.keys())
        y_water = self.df[self.keys[0]].values
        y_level = self.df[self.keys[2]].values

        dict_wl = {}
        for k in y_level:
            ks = str(k.__round__(2))
            if ks in dict_wl.keys():
                continue
            dict_wl[ks] = []

        wkeys = dict_wl.keys()

        num_data = len(y_level)
        for ks in wkeys:
            for idx in range(num_data):
                if str(y_level[idx].__round__(2)) == ks:
                    #print(y_water[idx])
                    dict_wl[ks].append(y_water[idx])

        save_dir = os.path.join(self.root_dir, save_filename)
        with open(save_dir,"w"):
            pass
        water_v = []
        level_v = []
        with open(save_dir,"a") as f:
            for ks in wkeys:
                wm = np.mean(dict_wl[ks]).__round__(4)
                if ks != '0' and wm !=0.0:
                    water_v.append(float(ks))
                    level_v.append(wm)
                    #print(wm)
                    f.write(ks+":"+str(wm)+"\n")

        data_dict = {"water":np.array(water_v),"level":np.array(level_v)}
        data_dict = pd.DataFrame(data_dict)
        data_dict = data_dict.sort_values(by="water", ascending=True)

        est = api.ols("water~level",data_dict).fit()
        y_pred = est.predict(data_dict["level"])
        data_dict["pred"] = y_pred.values
        scv_path = save_dir.replace(".txt",".csv")
        data_dict.to_csv(scv_path, index=False, encoding="gb2312")
        print(est.summary())
        # print(est.params)

        #draw([data_dict["level"],data_dict["water"],y_pred],"流量水位关系图",self.keys[0],self.keys[2],en_plot=True,en_scatter=True)

    def smooth(self,key="流速(m/s)",window_len=21,mode='savgol'):
        x = self.df[key]
        data_len = len(x)
        if data_len < window_len:
            pass
        if mode == "savgol":
            self.df[key] = signal.savgol_filter(x,window_len,4 if window_len > 10 else 2)
        else:
            results = []
            for idx in range(data_len-window_len):
                y = np.mean(x[idx:idx+window_len])
                results.append(y)
            idx += 1
            for i in range(window_len-1):
                y = np.mean(x[idx+i:idx+window_len])
                results.append(y)
            y = (results[-1]+x[-1])/2
            results.append(y)
            self.df[key] = np.array(results)

    def sort(self,key,ascending=True):
        #按给定键值排序y
        keys = self.df.keys()
        if key in keys:
            self.df = self.df.sort_values(by=key,ascending=ascending)

    def write(self):
        save_dir = os.path.join(self.root_dir,"backup_"+self.file)
        self.df.to_csv(save_dir,index=False,encoding="gb2312")

    def __call__(self):
        return self.df

if __name__ == "__main__":
    print("radar_data run")

    data_dir = "../data/铜仁/2020820-20201126FlowLevel.csv"
    # mode = RadarLevel(data_dir=flow_level_dir)
    # mode.smooth(key="流量(m3/s)", window_len=41)
    # data = mode()
    # data.to_csv(smooth_flow_level_dir, index=False, encoding="gb2312")
    # keys = ['流量(m3/s)', '面积(m2/s)', '水位(m)', '流速(m/s)', '时间']
    # data_original = pd.read_csv(flow_level_dir, engine="python")
    # data_smooth = pd.read_csv(smooth_flow_level_dir, engine="python")
    # x_time = data_original["时间"].values
    # data_original = data_original["流量(m3/s)"].values
    # data_smooth = data_smooth["流量(m3/s)"].values
    #
    # draw([x_time, data_original, data_smooth], title="数据平滑对比图", xlabel="时间", ylabel="流量",
    #      en_plot=True, en_scatter=True)
    #mode.water_level_relation()
