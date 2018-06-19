from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls import url
from django.views.static import serve
from . import views
import os

app_name = 'pec'

urlpatterns = [
    ## トップページ
    path('', views.index, name='index'),

    ## ダウンロードページ
    path('download/', views.download, name='download'),
    path('download/<int:subject_id>/', views.download_detail, name='download_detail'),

    ## アップロードページ
    path('upload/', views.upload, name='upload'),

    ## 編集トップ
    path('edit/', views.edit, name='edit'),

    # 編集 科目
    path('edit/subject/', views.edit_subject, name='edit_subject'),
    path('edit/subject/<int:subject_id>/', views.edit_subject_detail, name='edit_subject_detail'),

    # 編集 項目
    path('edit/exam_item/', views.edit_exam_item, name='edit_exam_item'),
    path('edit/exam_item/<int:exam_item_id>/', views.edit_exam_item_detail, name='edit_exam_item_detail'),

    # 編集 ファイル
    path('edit/file_data/', views.edit_file_data, name='edit_file_data'),
    path('edit/file_data/<int:file_data_id>', views.edit_file_data_detail, name='edit_file_data_detail'),
]

# 過去問のファイルが保存んされている場所
if settings.DEBUG:
    urlpatterns += [
       re_path(r'^kakomon/(?P<path>.*)$', serve, {
           'document_root': settings.PEC_KAKOMON_ROOT,
       }, name='kakomon'),
    ]
