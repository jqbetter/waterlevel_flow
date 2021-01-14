import os
import numpy as np
import pandas as pd

log_dirv= 'C:\\Users\\vmax\Desktop\\gzqV2.2.log'

station_id={
    '遵义赤水站':'60506800',
    '芜湖西河站':'62906101',
    '德阳高景关站':'6061440012',
    '宜宾孝儿站':'6050495012',
    '重庆寸滩站':'1040040004',
    '铜仁茅溪站':'61310520',
    '汉中马道站':'61806200',
    '山东源泉站':'41804550',
    '山东袁家站':'41803525',
}
# stcd=60506800 name=遵义赤水站
# stcd=62906101 name=芜湖西河站
# stcd=6061440012 name=德阳高景关站
# stcd=6050495012 name=宜宾孝儿站
# stcd=1040040004 name=重庆寸滩站
# stcd=61310520 name=铜仁茅溪站
# stcd=61806200 name=汉中马道站
# stcd=41804550 name=山东源泉站
# stcd=41803525 name=山东袁家站

f = open(log_dirv,'r')
ls = f.readlines()
print(type(ls))
f.close()