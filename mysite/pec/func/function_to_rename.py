
from django.conf import settings
import os
import shutil
import re


# 解答のみのファイルの名前の一部を _ans から +ans に変更する関数
# 解答のみのファイルの名前の一部を .\d. から (\d) に変更する関数
def rename_file():
    kakomon_path = settings.PEC_KAKOMON_ROOT
    for subject in os.listdir(kakomon_path):
        subject_path = os.path.join(kakomon_path, subject)
        for previous_file_name in os.listdir(subject_path):
            if previous_file_name.find('_ans') >= 0:
                previous_file_path = os.path.join(subject_path, previous_file_name)
                next_file_name = previous_file_name.replace('_ans', '^ans')
                next_file_path = os.path.join(subject_path, next_file_name)
                print(previous_file_name + ' -> ' + next_file_name)
                shutil.move(previous_file_path, next_file_path)
                previous_file_name = next_file_name
            line = previous_file_name.split('.')
            if len(line) == 3:
                match = re.findall(r'.*\.(\d+)\..*', previous_file_name)
                if len(match) == 1:
                    num = int(match[0])
                    next_file_name = line[0] + '(' + str(num) + ').' + line[2]
                    next_file_path = os.path.join(subject_path, next_file_name)
                    previous_file_path = os.path.join(subject_path, previous_file_name)
                    print(previous_file_name + ' -> ' + next_file_name)
                    shutil.move(previous_file_path, next_file_path)
