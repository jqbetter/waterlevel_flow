from __future__ import division
import numpy as np
import pandas as pd
from dataloader.utils import three_significant_figures
from scipy.optimize import leastsq
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import os


class fit_check(object):
    def __init__(self,station_name='',dir=None):
        super(fit_check, self).__init__()
        plt.rcParams['font.sans-serif'] = ['FangSong']  # 默认字体
        plt.rcParams['axes.unicode_minus'] = False  # 中文字符显示
        plt.rcParams['font.size'] = 13  # 字号
        self.station_name = station_name
        self.data = pd.read_csv(dir, engine='python')
        self.data = self.data.sort_values(by='测时水位')

    def func(self, a, x):
        return a[0]*x*x+ a[1]*x + a[2]

    def dist(self, a, x, y):
        return self.func(a, x) - y

    def LeaetSQ(self,x,y):
        params = leastsq(self.dist, [0, 0, 0], args=(x, y))[0]
        y_pred = self.func(params, x)
        r_square = 1 - np.sum((y - y_pred) ** 2) / np.sum((y - np.mean(y_pred)) ** 2)
        return params,r_square,y_pred

    def inverse_curve(self,a,y):
        temp = y - a[2]
        temp /= a[0]
        return np.power(temp,1/a[1])

    def curve(self,x,a,b,c):
        return a*np.power(x,b)+c

    def Curve_fit_result(self,x,y):
        params,_ = curve_fit(self.curve, x, y)
        x_pred = self.inverse_curve(params, y)
        y_pred = self.curve(x,params[0],params[1],params[2])
        r_square = 1 - np.sum((y - y_pred) ** 2) / np.sum((y - np.mean(y_pred)) ** 2)
        return params, r_square, x_pred

    def calculate_metric(self):

        f = open('./data/document/%s三检验和拟合数据.txt'%self.station_name, 'w')
        f.close()
        f = open('./data/document/%s三检验和拟合数据.txt'%self.station_name, 'a')
        data_z = self.data['测时水位'].values
        manual_q = self.data['实测流量'].values
        radar_q = self.data['雷达流量'].values
        #model = self.LeaetSQ(data_z, manual_q)
        # z = self.LeaetSQ(data_z, manual_q)
        # print(z)
        #self.Curve_fit_result(radar_q,data_z)

        # z_norm = (data_z - np.mean(data_z))/(data_z.max()-data_z.min())
        # mq_norm = (manual_q - np.mean(manual_q))/(manual_q.max()-manual_q.min())
        # rq_norm = (radar_q - np.mean(radar_q))/(radar_q.max()-radar_q.min())

        params,r_q,manual_pred = self.Curve_fit_result(manual_q,data_z)#self.LeaetSQ(manual_q, data_z)
        #print(params)
        #manual_pred = (manual_q.max()-manual_q.min())*manual_pred+np.mean(manual_q)
        #print("人工 ", r_q)

        f.write("人工拟合参数 z = %f *power(q, %f ) + %f\n" % (params[0], params[1], params[2]))
        f.write("人工拟合 r_square: " + str(r_q)+'\n')



        params,r_q,radar_pred = self.Curve_fit_result(radar_q,data_z)#self.LeaetSQ(radar_q, data_z)
        #radar_pred = (radar_q.max() - radar_q.min()) * radar_q + np.mean(radar_q)
        f.write("雷达拟合参数 z = %f *power(q, %f ) + %f\n" % (params[0], params[1], params[2]))
        #print("雷达 ",r_q)
        f.write("雷达拟合 r_square: "+ str(r_q)+'\n')

        f.write("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")
        number_data = len(data_z)

        deviate_value = radar_pred - radar_q
        mean_dv = np.mean(deviate_value)
        se = np.sqrt(np.sum((deviate_value / radar_pred) ** 2) / (number_data - 2))
        relative_error = deviate_value/radar_q
        f.write("随机不确定度 : %f\n" % (se * 2.0))
        f.write("系统误差 : %f\n" % np.mean(relative_error))

        number_pulse = len(np.where(relative_error>0.0001)[0]) + 0.5 * len(np.where(np.abs(relative_error)<=0.0001)[0])
        sign_u = (abs(number_pulse - 0.5 * number_data) - 0.5) / (0.5 * np.sqrt(number_data))

        number_sign_change = 0
        flag_pre = radar_q[0] - radar_pred[0]
        for idx in range(1, number_data):
            delta = radar_q[idx] - radar_pred[idx]
            if flag_pre > 0 and delta < 0:
                number_sign_change += 1
            elif flag_pre < 0 and delta > 0:
                number_sign_change += 1

            if delta == 0:
                pass
            else:
                flag_pre = delta

        f.write("样本量: %d ,正号个数: %.1f ,符号交换次数 : %d\n" % (number_data, number_pulse, number_sign_change))
        f.write("正负号检验: %.3f\n" % sign_u)
        if number_sign_change < 0.5 * (number_data - 1):
            fit_reg_u = (0.5 * (number_data - 1) - number_sign_change - 0.5) / (0.5 * np.sqrt(number_data - 1))
            f.write("适线检验: %.3f\n" % fit_reg_u)
        else:
            f.write("k>=0.5(n-1)，不做适线性检验\n")

        sp = deviate_value.std()
        deviation = mean_dv / sp
        f.write("偏离值检验: %.4f\n" % deviation)

        fig = plt.figure("draw_section_inforrmation",figsize=(10.24,6))
        axs = fig.add_subplot(1, 1, 1)

        l2 = axs.plot(manual_pred, data_z, c='r', label='人工拟合曲线')
        l4 = axs.plot(radar_pred, data_z, label='雷达拟合曲线')

        l1 = axs.scatter(manual_q, data_z, c='r', label='人工实测数据')
        l3 = axs.scatter(radar_q, data_z, label='雷达实测数据')

        axs.set_xlabel('流量$(m^3/s)$')
        axs.set_ylabel('水位$(m/s)$')

        lns = [l1 , l2[0] , l3 , l4[0]]

        labs = [l1.get_label(),l2[0].get_label(),l3.get_label(),l4[0].get_label()]
        plt.legend(lns, labs, loc=0)

        plt.grid()
        plt.subplots_adjust(top=0.95)
        # plt.show()
        plt.savefig("./data/figure/%s拟合曲线图.png"%self.station_name)
        plt.close()

        manual_q = np.array([three_significant_figures(x) for x in manual_q])
        radar_q = np.array([three_significant_figures(x) for x in radar_q])
        manual_pred = np.array([three_significant_figures(x) for x in manual_pred])
        radar_pred = np.array([three_significant_figures(x) for x in radar_pred])
        m_over_r = manual_pred / radar_pred
        relative_error = (radar_pred - manual_pred) / manual_pred

        f.close()
        #if not os.path.exists('./data/document/实测流量与雷达系统水位流量关系线系数分析.xlsx'):
        pd.DataFrame({"测时水位":data_z,
                  "实测流量":manual_q,
                  '实测流量线':manual_pred,
                  "雷达流量":radar_q,
                  '雷达流量线':radar_pred,
                  '实测流量线/雷达流量线':m_over_r,
                  '相对误差':relative_error}).to_excel('./data/document/%s实测流量与雷达系统水位流量关系线系数分析.xlsx'%self.station_name,index=False,encoding='gb232')


class fit_check_no_manual(object):
    def __init__(self,station_name='',dir=None):
        super(fit_check_no_manual, self).__init__()
        plt.rcParams['font.sans-serif'] = ['FangSong']  # 默认字体
        plt.rcParams['axes.unicode_minus'] = False  # 中文字符显示
        plt.rcParams['font.size'] = 13  # 字号
        self.station_name = station_name
        self.data = pd.read_csv(dir, engine='python')
        self.data = self.data.sort_values(by='水位')

    def func(self, a, x):
        return a[0]*x*x+ a[1]*x + a[2]

    def dist(self, a, x, y):
        return self.func(a, x) - y

    def LeaetSQ(self,x,y):
        params = leastsq(self.dist, [0, 0, 0], args=(x, y))[0]
        y_pred = self.func(params, x)
        r_square = 1 - np.sum((y - y_pred) ** 2) / np.sum((y - np.mean(y_pred)) ** 2)
        return params,r_square,y_pred

    def inverse_curve(self,a,y):
        temp = y - a[2]
        temp /= a[0]
        return np.power(temp,1/a[1])

    def curve(self,x,a,b,c):
        return a*np.power(x,b)+c

    def Curve_fit_result(self,x,y):
        params,_ = curve_fit(self.curve, x, y)
        x_pred = self.inverse_curve(params, y)
        y_pred = self.curve(x,params[0],params[1],params[2])
        r_square = 1 - np.sum((y - y_pred) ** 2) / np.sum((y - np.mean(y_pred)) ** 2)
        return params, r_square, x_pred

    def calculate_metric(self):
        f = open('./data/document/%s三检验和拟合数据.txt'%self.station_name, 'w')
        f.close()
        f = open('./data/document/%s三检验和拟合数据.txt'%self.station_name, 'a')
        data_z = self.data['水位'].values
        radar_q = self.data['流量'].values

        params,r_q,radar_pred = self.Curve_fit_result(radar_q,data_z)#self.LeaetSQ(radar_q, data_z)
        #radar_pred = (radar_q.max() - radar_q.min()) * radar_q + np.mean(radar_q)
        f.write("雷达拟合参数 z = %f *power(q, %f ) + %f\n" % (params[0], params[1], params[2]))
        #print("雷达 ",r_q)
        f.write("雷达拟合 r_square: "+ str(r_q)+'\n')

        f.write("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")
        number_data = len(data_z)

        deviate_value = radar_pred - radar_q
        mean_dv = np.mean(deviate_value)
        se = np.sqrt(np.sum((deviate_value / radar_pred) ** 2) / (number_data - 2))
        relativate_error = deviate_value/radar_q
        f.write("随机不确定度 : %f\n" % (se * 2.0))
        f.write("系统误差 : %f\n" % np.mean(relativate_error))
        number_pulse = len(np.where(relativate_error>0.0001)[0]) + 0.5 * len(np.where(np.abs(relativate_error)<=0.0001)[0])
        sign_u = (abs(number_pulse - 0.5 * number_data) - 0.5) / (0.5 * np.sqrt(number_data))

        number_sign_change = 0
        flag_pre = radar_q[0] - radar_pred[0]
        for idx in range(1, number_data):
            delta = radar_q[idx] - radar_pred[idx]
            if flag_pre > 0 and delta < 0:
                number_sign_change += 1
            elif flag_pre < 0 and delta > 0:
                number_sign_change += 1

            if delta == 0:
                pass
            else:
                flag_pre = delta


        f.write("样本量: %d ,正号个数: %.1f ,符号交换次数 : %d\n" % (number_data, number_pulse, number_sign_change))
        f.write("正负号检验: %.3f\n" % sign_u)
        if number_sign_change < 0.5 * (number_data - 1):
            fit_reg_u = (0.5 * (number_data - 1) - number_sign_change - 0.5) / (0.5 * np.sqrt(number_data - 1))
            f.write("适线检验: %.3f\n" % fit_reg_u)
        else:
            f.write("k>=0.5(n-1)，不做适线性检验\n")

        sp = deviate_value.std()
        # print("mean",mean_dv)
        # print("标准差",sp)
        deviation = mean_dv/sp
        f.write("偏离值检验: %.4f\n" % deviation)

        fig = plt.figure("draw_section_inforrmation",figsize=(10.24,6))
        axs = fig.add_subplot(1, 1, 1)

        axs.scatter(radar_q, data_z, label='雷达实测数据',c='orange')
        axs.plot(radar_pred, data_z, label='雷达拟合曲线',c='g')

        axs.set_xlabel('流量$(m^3/s)$')
        axs.set_ylabel('水位$(m/s)$')

        plt.legend()
        plt.grid()
        plt.subplots_adjust(top=0.95)
        # plt.show()
        plt.savefig("./data/figure/%s拟合曲线图.png"%self.station_name)
        plt.close()

        #manual_q = np.array([three_significant_figures(x) for x in manual_q])
        radar_q = np.array([three_significant_figures(x) for x in radar_q])
        #manual_pred = np.array([three_significant_figures(x) for x in manual_pred])
        radar_pred = np.array([three_significant_figures(x) for x in radar_pred])
        #m_over_r = manual_pred / radar_pred
        #relative_error = (radar_pred - manual_pred) / manual_pred

        f.close()
        #if not os.path.exists('./data/document/实测流量与雷达系统水位流量关系线系数分析.xlsx'):
        pd.DataFrame({"测时水位":data_z,
                  #"实测流量":manual_q,
                  #'实测流量线':manual_pred,
                  "雷达流量":radar_q,
                  '雷达流量线':radar_pred}
                  ).to_excel('./data/document/%s实测流量与雷达系统水位流量关系线系数分析.xlsx'%self.station_name,index=False,encoding='gb232')

if __name__ == "__main__":
    print("fitting function")
    z = np.power(2,1/0.5)
    print(z)