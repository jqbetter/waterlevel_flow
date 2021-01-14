import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import datetime
import numpy as np
import math


def draw_init():
    plt.rcParams['font.sans-serif'] = ['FangSong']  # 默认字体
    plt.rcParams['axes.unicode_minus'] = False  # 中文字符显示
    plt.rcParams['font.size'] = 16  # 字号

def draw_radar_install_point(distance, high, install_point, save_dir=None):
    # max_level_text = "历史最高水位%.2fm"%(max_level)
    # min_level_text = "历史最低水位%.2fm"%(min_level)
    # x_text_axis = distance.min() + (distance.max()-distance.min())//2 - len(max_level_text)

    #x_ticks_step = (distance.max() - distance.min()) // 5
    y_ticks_step = int((high.max() - high.min()) / 4)
    # print(y_ticks_step)
    # x_ticks = np.arange(0, distance.max()+10, 20)
    # x_ticks[-1] = distance[-1]
    # print(int(high.min()),max(high.max(),install_point[1]+2))
    y_ticks = np.arange(int(high.min()), max(high.max(), install_point[1] + 2), y_ticks_step)

    fig = plt.figure("draw_section_inforrmation",figsize=(10.24,8))
    axs = fig.add_subplot(1, 1, 1)
    # plt.title("断面信息")
    axs.set_xlabel("起点距($m$)")
    axs.set_ylabel("河底高程($m$)")

    # axis = [min(install_point[0],distance.min())-2,distance.max(),high.min()-2,install_point[1]+2]
    # print(axis)
    # plt.axis(axis)
    # plt.grid(args["grid"])
    # axs.set_xticks(x_ticks)
    # print(min(high))
    # print(high[-1])
    # print((min(high[0] + high[-1]) + min(high)) / 2)
    axs.set_yticks(y_ticks)
    axs.set_xlim(min(install_point[0],distance[0]), distance[-1])
    axs.set_ylim(y_ticks[0], max(install_point[1],y_ticks[-1])+1)

    axs.scatter(install_point[0], install_point[1], s=68,c='r',marker='D')
    axs.text(install_point[0] + 2, install_point[1]-0.5, "测扫雷达安装位置\n(%.1f,%.1f)" % (install_point[0], install_point[1]),size=18)
    axs.fill_between(distance, 0,(min(high[0],high[-1])+min(high))/2, color='#B0DBE6')
    axs.fill_between(distance, y1=0, y2=high, color='#8C5959')
    # plt.axhline(max_level,c="g")
    # plt.text(x_text_axis, max_level+0.5,max_level_text)
    # plt.axhline(min_level,c='orange')
    # plt.text(x_text_axis, min_level+0.5,min_level_text)

    #plt.grid()
    # plt.axis('off')
    # plt.subplots_adjust(top=1,bottom=0,left=0,right=1,hspace=0,wspace=0)
    plt.subplots_adjust(top=0.95)
    # axs.spines['right'].set_visible(False)
    # axs.spines['top'].set_visible(False)
    #plt.show()
    if save_dir != None:
        plt.savefig(save_dir)
        plt.close()
    else:
        plt.show()


def draw_section_level_information(distance, high, max_level, min_level,save_dir=None):
    max_level_text = "历史最高水位%.2fm" % (max_level)
    min_level_text = "历史最低水位%.2fm" % (min_level)

    y_ticks_step = int((max(high.max(),max_level) - high.min()) / 4)
    # print(y_ticks_step)
    # x_ticks = np.arange(0, distance.max()+10, 20)
    # x_ticks[-1] = distance[-1]
    # print(int(high.min()),max(high.max(),install_point[1]+2))
    y_ticks = np.arange(int(high.min()), max(high.max(),max_level)+y_ticks_step, y_ticks_step)



    fig = plt.figure("draw_section_level_information",figsize=(10.24,8))
    #print(help(fig))
    axs = fig.add_subplot(1, 1, 1)
    # plt.title("断面信息")
    axs.set_xlabel("起点距($m$)")
    axs.set_ylabel("河底高程($m$)")

    # axis = [min(install_point[0],distance.min())-2,distance.max(),high.min()-2,install_point[1]+2]
    # print(axis)
    # plt.axis(axis)
    # plt.grid(args["grid"])
    # axs.set_xticks(x_ticks)
    axs.set_yticks(y_ticks)
    axs.set_xlim(distance[0],distance[-1])
    axs.set_ylim(y_ticks[0], max(max_level,y_ticks[-1])+1)
    # plt.scatter(install_point[0], install_point[1], s=100)
    # plt.text(install_point[0] + 2, install_point[1] - 1, "测扫雷达安装位置\n(%.2f,%.2f)" % (install_point[0], install_point[1]))
    axs.fill_between(distance, max_level, max_level+0.05, color='r')
    axs.fill_between(distance, 0, (min(max_level,high[0])+min_level)/2, color='#B0DBE6')
    axs.fill_between(distance, min_level, min_level + 0.05, color='b')
    axs.fill_between(distance, y1=0, y2=high, color='#8C5959')

    x_text_axis = (distance[0]+distance[-1]+1)//2 - 50
    #print(x_text_axis)
    # axs.plot(distance, high, color="r")
    # axs.axhline(max_level, c="g")
    axs.text(x_text_axis, max_level + 0.25, max_level_text,size=18)
    # axs.axhline(min_level, c='orange')
    axs.text(x_text_axis, min_level + 0.25, min_level_text,size=18)
    #axs.fill_between(distance,high,y_ticks[0],facecolor='#D2691E')

    #plt.grid()
    plt.subplots_adjust(top=0.95)
    # axs.spines['right'].set_visible(False)
    # axs.spines['top'].set_visible(False)
    if save_dir != None:
        plt.savefig(save_dir)
        plt.close()
    else:
        plt.show()

def signal_over_noise_bar(data_rate=None,save_dir=None):
    max_y = data_rate.max()

    y_tricks = np.arange(0,10*(math.ceil(max_y/10)+1),10)

    # plt.rcParams['font.sans-serif'] = ['FangSong']  # 默认字体
    # plt.rcParams['axes.unicode_minus'] = False  # 中文字符显示
    # plt.rcParams['font.size'] = 13  # 字号
    fig = plt.figure("signal_over_noise_bar",figsize=(10.24,6))
    axs = fig.add_subplot(1, 1, 1)
    #axs.set_title("测扫雷达各分段信噪比分布柱状图")
    #plt.title("测扫雷达各分段信噪比分布柱状图")
    # plt.xlabel("有效率分布区间(%)")
    # plt.ylabel("分布频率(%)")
    axs.set_xlabel("置信度分布区间(%)")
    axs.set_ylabel("分布频率(%)")
    #x_tricks = [5, 15, 25, 35, 45, 55, 65, 75, 85, 95]
    x_tricks = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    axs.bar(x_tricks, data_rate, width=5)
    axs.set_yticks(y_tricks)
    axs.set_xticks(x_tricks)#np.arange(0, 110, 10))
    # for idx in range(10):
    #     str_text = "%.2f"%data_rate[idx]
    #     axs.text(x_tricks[idx]-len(str_text)*0.5-1.5, data_rate[idx],str_text)

    #axs.spines['left'].set_visible(False)
    axs.spines['right'].set_visible(False)
    axs.spines['top'].set_visible(False)
    plt.subplots_adjust(top=0.95)

    plt.grid(axis='y',linestyle='--')
    if save_dir != None:
        plt.savefig(save_dir)
        plt.close()
    else:
        plt.show()

def section_velocity_diagram(x1,y1,x2,y2,save_dir=None):
    max_dis = max(x1)
    #x_trick = np.arange(10,max_dis+10,20)
    fig = plt.figure("section_velocity_diagram",figsize=(10.24,8))
    axs = fig.add_subplot(1, 1, 1)
    #axs.set_title("截面流速图")
    axs.set_xlabel("起点距($m$)")
    axs.set_ylabel("流速($m/s$)")
    l1= axs.plot(x1,y1,c='orange',label="分段流速")
    #axs.set_xticks(x_trick)

    ax2 = axs.twinx()
    l2 = ax2.plot(x2,y2,label="高程")
    ax2.set_ylabel("高程(m)")

    lns = l1+l2
    labs = [l.get_label() for l in lns]
    plt.legend(lns,labs,loc=0)
    plt.subplots_adjust(top=0.95)
    plt.grid()
    #axs.spines['right'].set_visible(False)
    # axs.spines['top'].set_visible(False)
    # ax2.spines['top'].set_visible(False)
    if save_dir != None:
        plt.savefig(save_dir)
        plt.close()
    else:
        plt.show()


def level_q_timing_diagram(time_str, level, q_value, sq_value,save_dir=None):
    #mid_local = len(index)//2
    #x_trick = np.array([datetime.datetime.strptime(x[:10],"%Y/%m/%d") for x in time_str])
    x_trick = []
    for x in time_str:
        t = datetime.datetime.strptime(x[:10].split(' ')[0],"%Y/%m/%d")
        x_trick.append(t)
    x_trick = np.array(x_trick)
    # print(x_trick)
    fig = plt.figure("level_q_timing_diagram",figsize=(12.4,8))
    axs = fig.add_subplot(1, 1, 1)
    #axs.set_title("截面流速图")
    axs.set_xlabel("日期")
    axs.set_ylabel("流量($m^3/s$)")

    l1 = axs.plot(x_trick, q_value, c='orange', label="原始流量")
    l2 = axs.plot(x_trick, sq_value, c='g', label='平滑流量')
    xfmt = mdates.DateFormatter("%y-%m-%d")
    axs.xaxis.set_major_formatter(xfmt)
    #axs.set_xticks(x_trick)

    ax2 = axs.twinx()
    ax2.set_ylabel("水位($m$)")
    l3 = ax2.plot(x_trick, level, c='b', label="水位")

    lns = l1 + l2+ l3
    labs = [l.get_label() for l in lns]
    plt.legend(lns, labs, loc=0)
    plt.subplots_adjust(top=0.95)
    plt.grid()
    # axs.spines['right'].set_visible(False)
    # axs.spines['top'].set_visible(False)
    # ax2.spines['top'].set_visible(False)
    #plt.show()
    if save_dir != None:
        plt.savefig(save_dir)
        plt.close()
    else:
        plt.show()

if __name__ == "__main__":
    print("test draw")
    # draw_init()
    # section_dir = "E:\VMAX\chishui\data\赤水截面.csv"
    #
    # sec_data = pd.read_csv(section_dir, engine="python")
    # distance = sec_data["起点距"].values
    # high = sec_data["高程"].values
    #
    # max_level = 227.67
    # min_level = 223.48
    # install_point = (0, 235.8)
    # draw_section_inforrmation(distance,high,(0,237))
    # s = '2020/5/20 '
    # ss = s.rstrip()
    # t = datetime.datetime.strptime(ss,'%Y/%m/%d')
    # print(t)

    plt.figure()
    x = np.array([1,2,3,4,5,6,7,8,9])
    y = np.array([2,4,6,8,10,12,14,16,18])

    plt.fill_between(x, 11,11.1,color='r')
    plt.fill_between(x, 0, 10, color='#B0DBE6')
    plt.fill_between(x, 0, y2=y, color='#8C5959')
    plt.show()