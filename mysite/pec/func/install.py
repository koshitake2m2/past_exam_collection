
from django.conf import settings
from pec.models import Subject, Exam_item, Exam_item, Year, File_data
import os
import shutil
import sys
import datetime
import re

def init_subject():
    '''
    モデルSubjectの初期化をする関数
    科目の情報（英語名、和名、ふりがな）の記述がされているファイル'subject.txt'を
    読み込んで、科目のインスタンスを作る
    '''
    # DB の初期化
    for line in Subject.objects.all():
        line.delete()

    # 過去問がおいてあるルートディレクトリのパス
    kakomon_path = settings.PEC_KAKOMON_ROOT
    # 過去問がある科目のリスト
    existing_subject_list = os.listdir(kakomon_path)

    # 科目の情報が記述されているファイルへのパス
    subject_txt_path = os.path.join(settings.PEC_DATA_PATH, 'subject.txt')
    for line in open(subject_txt_path).readlines():
        subject = line.rstrip('\n').split(' ')
        print(subject)

        # この科目の過去問が存在するか
        exists = False
        if subject[0] in existing_subject_list:
            exists = True

        # インスタンス作成
        Subject(
        name_en=subject[0],
        name_jp=subject[1],
        name_hiragana=subject[2],
        exists=exists
        ).save()

def init_exam_item():
    '''
    モデルExam_itemの初期化をする関数
    項目の情報（順序、英語名、和名）の記述がされているファイル'exam_item.txt'を
    読み込んで、項目のインスタンスを作る
    '''
    # DB の初期化
    for line in Exam_item.objects.all():
        line.delete()

    # 項目の情報が記述されているファイルへのパス
    exam_item_txt_path = os.path.join(settings.PEC_DATA_PATH, 'exam_item.txt')
    for line in open(exam_item_txt_path).readlines():
        exam_item = line.rstrip('\n').split(' ')
        print(exam_item)

        # インスタンス作成
        Exam_item(
        order=int(exam_item[0]),
        name_en=exam_item[1],
        name_jp=exam_item[2]
        ).save()

def get_wareki(seireki):
    '''
    西暦を渡して和暦を返す関数
    '''
    if seireki == '0000':
        wareki = '年不明'
    elif int(seireki) <= 1925:
        wareki = str(seireki)
    elif 1925 < int(seireki) <= 1988:
        wareki = 'S'+str(int(seireki)-1925) # 昭和のS
    elif 1988 < int(seireki) <= 2018:
        wareki = 'H'+str(int(seireki)-1988) # 平成のH
    elif 2018 < int(seireki):
        wareki = 'X'+str(int(seireki)-2018) # 新しい年号は？
    return wareki

def init_year():
    '''
    モデルYearの初期化をする関数
    年度の情報（西暦、和暦）
    1980~現在の西暦までのインスタンスを作成する関数
    '''
    # DB init
    for line in Year.objects.all():
        line.delete()

    # 年不明の年度インスタンス作成
    seireki = '0000'
    wareki = get_wareki(seireki)
    Year(
    name_en=seireki,
    name_jp=wareki
    ).save()

    this_year = datetime.date.today().year
    # existing_year は 1980 ~ 現在の西暦
    for seireki in range(1980, this_year+1):
        wareki = get_wareki(str(seireki))
        print(seireki, wareki)
        # 年度インスタンス作成
        Year(
        name_jp=wareki,
        name_en=str(seireki)
        ).save()

def init_file_data():
    '''
    モデルFile_dataの初期化をする関数
    ファイルの情報（科目、年度、項目、解答の如何、重複ファイル（名前が同じもの）の存在、
    拡張子、ファイル名、サイズ、最終更新日）
    ファイルの情報を格納したインスタンスを作成
    '''
    # DB init
    for line in File_data.objects.all():
        line.delete()

    # 過去問があるルートディレクトリ
    kakomon_path = settings.PEC_KAKOMON_ROOT

    # 過去問ディレクトリ下にあるファイルについて一つ一つ走査して、
    # 情報を調べてインスタンスを作成する
    for subject_name in os.listdir(kakomon_path):
        # 科目のインスタンス
        subject = Subject.objects.get(name_en=subject_name)
        # 科目があるディレクトリのパス
        subject_path = os.path.join(kakomon_path, subject_name)
        for file_name in os.listdir(subject_path):
            file_path = os.path.join(subject_path, file_name)

            # 拡張子を取得する。拡張子がなかったらなしで登録
            if file_name.find('.') >= 0:
                part_of_file_name, extension = file_name.split('.', 1)
                extension = '.' + extension
            else:
                part_of_file_name, extension = file_name, ''

            if len(part_of_file_name.split('-')) != 3:
                # 不適切なフォーマットです
                print(file_name + ' は\'-\'において不適切なフォーマットです')
                continue

            # 年度、項目のインスタンス、項目に付与される番号、解答のみの如何、重複ファイル
            seireki, part_of_exam_item = part_of_file_name.split('-')[1:3]
            year = Year.objects.get(name_en=seireki)

            # 重複ファイル: ex) mid2^ans(3) の()の中の数字を抜き出す
            match = re.findall('\((\d+)\)', part_of_exam_item)
            if len(match) == 0:
                same_name_number = 0
            else:
                same_name_number = match[-1]

            part_of_exam_item = part_of_exam_item.split('(')[0]
            tmp = part_of_exam_item

            # 解答のみの如何: ex) mid2^ans
            only_ans = False
            if part_of_exam_item.find('^ans') >= 0:
                only_ans = True

            part_of_exam_item = part_of_exam_item.replace('^ans', '')
            match = re.findall(r'(\d+|\D+)', part_of_exam_item)

            # 項目に付与される番号（連番）: ex) mid2 の 2 の部分
            exam_item_number = 0
            exma_item_name_en = part_of_exam_item

            if len(match) == 1 and not match[0].isdecimal():
                exam_item_name_en = match[0]
            elif len(match) == 2 and not match[0].isdecimal() and match[1].isdecimal():
                exam_item_name_en = match[0]
                exam_item_number = match[1]
            else:
                print(file_name + ' は連番において不適切なフォーマットです')
                continue

            # 項目のインスタンス
            exam_item = Exam_item.objects.get(name_en=exam_item_name_en)

            # ファイルサイズ
            size = os.path.getsize(file_path)
            unit = 'B'
            if size // 1024 != 0:
                size /= 1024
                unit = 'KB'
                if size // 1024 != 0:
                    size /= 1024
                    unit = 'MB'
            size = str(round(size, 2)) + unit

            # 最終更新日
            dt = datetime.datetime.fromtimestamp(os.stat(file_path).st_mtime)
            reset_day = dt.strftime('%Y/%m/%d %H:%M:%S')

            # テスト ファイル名
            file_name_en = '-'.join([subject.name_en, year.name_en, exam_item.name_en])
            if exam_item_number != 0:
                file_name_en += str(exam_item_number)

            if only_ans:
                file_name_en += '^ans'

            if same_name_number != 0:
                file_name_en += '('+same_name_number+')'

            file_name_en += extension

            if file_name != file_name_en:
                print(file_name)
            print(file_name)

            subject.file_data_set.create(
            subject=subject,
            year=year,
            exam_item=exam_item,
            exam_item_number=exam_item_number,
            only_ans=only_ans,
            same_name_number=same_name_number,
            extension=extension,
            file_name=file_name,
            size=size,
            reset_day=reset_day
            ).save()

def init_all():
    '''
    全てのモデルを初期化する関数
    '''
    init_subject()
    init_exam_item()
    init_year()
    init_file_data()

def main():
    pass

if __name__ == '__main__':
    main()
