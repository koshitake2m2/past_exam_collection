from django import forms

class UploadFileForm(forms.Form):
    '''
    アップロードファイルのためのフォーム
    '''
    file = forms.FileField()

class SubjectForm(forms.Form):
    '''
    科目情報の変更のためのフォーム
    新しく科目を追加するときにも使用可能
    '''
    subject_name_en = forms.CharField(max_length=80, widget=forms.TextInput(attrs={'size':60}))
    subject_name_jp = forms.CharField(max_length=80, widget=forms.TextInput(attrs={'size':60}))
    subject_name_hiragana = forms.CharField(max_length=80, widget=forms.TextInput(attrs={'size':60}))

class Exam_itemForm(forms.Form):
    '''
    項目情報の変更のためのフォーム
    '''
    exam_item_order = forms.IntegerField()
    exam_item_name_en = forms.CharField(max_length=80, widget=forms.TextInput(attrs={'size':60}))
    exam_item_name_jp = forms.CharField(max_length=80, widget=forms.TextInput(attrs={'size':60}))
