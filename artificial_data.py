#codeing = utf-8
import numpy as np
import csv
import pandas as pd
import scipy.signal as signal
import random
import xlrd
import xlwt
from datetime import datetime
import os
import re

data_dir = "../data/202061.xls"
folder_dir = "../data/"

class ReadExcel:
    def __init__(self,file_dir = data_dir):
        super(ReadExcel, self).__init__()
        assert os.path.exists(file_dir), "The file does not exist in the data_dir path."
        self.data_dir = file_dir
        self.workBook = xlrd.open_workbook(self.data_dir)
        self.allSheetNames = self.workBook.sheet_names()
        self.sheet = self.workBook.sheet_by_name(self.allSheetNames[1])
        self.nrows = self.sheet.nrows
        self.nclos = self.sheet.ncols
        self.keys_str = ["断面流量", "断面面积", "平均流速", "最大流速"]
        self.data_dict = {}
        self.data_dict = {"采集时间": "2020-" + self.get_date()}
        self.hydrological_information()

    def get_date(self):
        regular_expression = r"(\d{1,2} 月 \d{1,2} 日 \d{1,2} 时 \d{1,2} 分 至 \d{1,2} 时 \d{1,2} 分)"
        cells = self.sheet.row_values(self.sheet.nrows - 1)
        date = re.findall(regular_expression, cells[2])[0]
        date = date.replace(" ", "")
        date = date.replace("月", "-")
        date = date.replace("日", " ")
        date = date.replace("时", ":")
        date = date.replace("分", "")
        date = date.replace("至", " to ")
        return date

    def hydrological_information(self):
        col_values = self.sheet.col_values(0)
        for key in self.keys_str:
            p = col_values.index(key)
            cells = self.sheet.row_values(p)
            #print(cells)
            if key == "断面面积":
                l = cells.index("基 本")
                d = cells[l:]
                for e in d:
                    if type(e) == float:
                        self.data_dict["水位"] = e
                        continue
            self.data_dict[key] = cells[2]

    def __call__(self):
        return self.data_dict

class ArtificialLoader:
    def __init__(self,folder_dir = folder_dir):
        super(ArtificialLoader, self).__init__()
        self.folder = folder_dir
        self.file_list = os.listdir(self.folder)
        self.select_file()
        self.work = ReadExcel
        self.data = self.read_data()

    def select_file(self):
        for x in self.file_list:
            if not ".xls" in x or ".xlsx" in x:
                self.file_list.remove(x)

    def read_data(self):
        for x in self.file_list:
            work = self.work(os.path.join(self.folder, x))
            yield work()

    def process(self,save_dir="../data/save.csv"):
        keys = self.data.__next__().keys()
        pd_date = {}
        for key in keys:
            pd_date[key] = []
        for t in self.data:
            for key in keys:
                pd_date[key].append(t[key])
        for key in keys:
            y = np.array(pd_date[key])
            pd_date[key] = y
        save_file = pd.DataFrame(pd_date)
        save_file.to_csv(save_dir,index=False,encoding="gb2312")
        return keys,pd_date

    def __call__(self):
        #print(len(self.file_list))
        return self.data


if __name__ == "__main__":
    print("test run")
    x_dir = "../chishui/data/赤水/赤水缆道实测流量计算表12.4(1).xls"
    z = ReadExcel(x_dir)()
    print(z)