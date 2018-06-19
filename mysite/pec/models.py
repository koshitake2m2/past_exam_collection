import datetime
from django.db import models
from django.utils import timezone

import uuid


# 科目
class Subject(models.Model):
    # 科目名の英語名
    name_en = models.CharField(max_length=80)

    # 科目名の和名
    name_jp = models.CharField(max_length=80)

    # 科目名のふりがな
    name_hiragana = models.CharField(max_length=80)

    # この科目の過去問が存在するか
    exists = models.BooleanField(default=False)

    def __str__(self):
        return self.name_en

# 年度
class Year(models.Model):
    # 西暦年度
    name_en = models.CharField(max_length=80)

    # 和暦年度
    name_jp = models.CharField(max_length=80)

    def __str__(self):
        return self.name_en

# 項目
class Exam_item(models.Model):
    # 整列するときの順序: 数値が低いほど前
    order = models.IntegerField()

    # 項目の英語名:
    # 文字列のみ, 数値はいれてはならない
    name_en = models.CharField(max_length=80)

    # 項目の日本語名
    name_jp = models.CharField(max_length=80)

    def __str__(self):
        return self.name_en

# ファイルのデータ
class File_data(models.Model):
    # 科目: ex) アルゴリズムとデータ構造II, AlgorithmAndDataStructureII
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    # 年度: ex) H30, 2018
    year = models.ForeignKey(Year, on_delete=models.CASCADE)

    # 項目: ex) 中間試験, mid
    exam_item = models.ForeignKey(Exam_item, on_delete=models.CASCADE)

    # 項目に付与される番号: ex) 中間試験2, mid2 の 2 の部分
    exam_item_number = models.IntegerField(default=0)

    # 解答のみか否か: ex) 中間試験^解答, mid^ans
    # ファイルが解答のみの場合に付与される
    only_ans = models.BooleanField(default=False)

    # 重複ファイル: ex) 中間試験(3), mid(3)
    # 同じ名前のファイルがあるとき付与される
    same_name_number = models.IntegerField(default=0)

    # 拡張子: ex) .pdf
    extension = models.CharField(max_length=20)

    # ファイル名: ex) AlgorithmAndDataStructureII-2018-mid2^ans(3).pdf
    file_name = models.CharField(max_length=80)

    # ファイルのサイズ: ex) 495KB
    size = models.CharField(max_length=80)

    # ファイルの最終更新日: ex) 2018/04/24 19:22:40
    reset_day = models.CharField(max_length=80)

    def __str__(self):
        return self.file_name
