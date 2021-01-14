import pandas as pd
import numpy as np
import datetime
import scipy.signal as signal
import re


def count_days(start,deadline):
    # months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    # ys, ms, ds = [int(s) for s in re.findall(r"\d+", start)]
    # yd, md, dd = [int(s) for s in re.findall(r"\d+", deadline)]
    # assert yd >= ys, "year error"
    # if yd == ys:
    #     assert md >= ms, "month error"
    #     if md == ms:
    #         assert dd > ds, "day error"
    # days = 0
    # if md > ms+1:
    #     for idx in range(ms+1,md):
    #         days += months[idx]
    # days += dd
    # days += months[ms]-ds+1
    d1 = datetime.datetime.strptime(start, "%Y-%m-%d")
    d2 = datetime.datetime.strptime(deadline, "%Y-%m-%d")
    days = d2-d1
    days = days.days
    return days

def str_to_date(str):
    y, m, d = [int(s) for s in re.findall(r"\d+", str)]
    return datetime.date(y, m, d)

def data_smoothing(q_value,window_len=21,mode='savgol'):
    data_len = len(q_value)
    if data_len < window_len:
        pass
    if mode == "savgol":
        smooth_q = signal.savgol_filter(q_value,window_len,4 if window_len > 10 else 2)
    else:
        results = []
        for idx in range(data_len-window_len):
            y = np.mean(q_value[idx:idx+window_len])
            results.append(y)
        idx += 1
        for i in range(window_len-1):
            y = np.mean(q_value[idx+i:idx+window_len])
            results.append(y)
        y = (results[-1]+q_value[-1])/2
        results.append(y)
        smooth_q = np.array(results)
    return smooth_q

def process_by_confidence(original_dir,dest_dir,confidence=0.8):
    df = pd.read_csv(original_dir, encoding="gb2312")
    keys = ['分段距离(m)','置信度']
    #print(self.df.keys())
    y_dest = df[keys[0]].values
    y_confidence = df[keys[1]].values
    ls = np.where(y_dest == 100.)[0]

    step = ls[1]-ls[0]

    clear_list_flag = []
    clear_list = []
    for l in ls:
        if y_confidence[l] < confidence:
            clear_list_flag.append(l)
    for t in clear_list_flag:
        for i in range(t - 9, t + step-9):
            clear_list.append(i)

    clear_list.sort(reverse=True)
    for idx in clear_list:
        df = df.drop(idx)
    #self.df = pd.read_csv(self.dir, skiprows=clear_list, encoding="gb2312")
    #print(self.df)
    df.to_csv(dest_dir,index=False,encoding="gb2312")

def process_by_date(original_dir,dest_dir,start="2020-8-25",deadline="2020-11-11"):
    df = pd.read_csv(original_dir, encoding="gb2312")
    # print(self.df)
    start_date = str_to_date(start)
    deadlines = str_to_date(deadline)
    clear_list = []

    y_date = df["时间"].values
    # print(y_date)
    num_data = len(y_date)
    for idx in range(num_data):
        str_c = y_date[idx].split(" ")[0]
        current_date = str_to_date(str_c)
        if current_date < start_date:
            clear_list.append(idx)
        if current_date > deadlines:
            clear_list.append(idx)

    clear_list.sort(reverse=True)
    for idx in clear_list:
        df = df.drop(idx)
    # self.df = pd.read_csv(self.dir, skiprows=clear_list,)
    df.to_csv(dest_dir,index=False,encoding="gb2312")

def three_significant_figures(x):
    z = abs(x)
    try:
        if z < 1:
            y = x.__round__(3)
        elif z < 10:
            y = x.__round__(2)
        elif z <100:
            y = x.__round__(1)
        elif z < 1000:
            y = x.__round__(0)
            y = int(y)
        else:
            x = x/10
            x = x.__round__(0)
            y = 10*x
            y = int(y)
        return y
    except:
        return 0

def collect_dis_data(dis_dir):
    dis_data = pd.read_csv(dis_dir, engine="python")
    iters = dis_data.index
    dis_date = dis_data['时间'].values
    dis_distance = dis_data['分段距离(m)'].values
    dis_velocity = dis_data['流速(m/s)'].values
    dis_confidence = dis_data['置信度'].values
    dis_proportion = dis_data['占比'].values
    dis_dict = {}
    # 字典，存储同一时间下的分段流速信息，字典值为列表
    # 同一时间的相同分段距离信息存放于一个元组，元组内容依次为分段距离，对应流速，置信度，占比
    for idx in iters:
        dis_tuple = dis_distance[idx], dis_velocity[idx], dis_confidence[idx] ,dis_proportion[idx]
        if not dis_date[idx] in dis_dict.keys():
            dis_dict[dis_date[idx]] = []
        dis_dict[dis_date[idx]].append(dis_tuple)
    return dis_dict
