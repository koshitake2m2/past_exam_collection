from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.conf import settings

from .models import Subject, Exam_item, Year, File_data
import datetime
import os
import shutil

from .forms import UploadFileForm
from .forms import SubjectForm
from .forms import Exam_itemForm

def index(request):
    '''
    トップページ
    '''
    return render(request, 'pec/index.html')

def download(request):
    '''
    ダウンロードしたい科目を選択するページ
    '''
    # 過去問が存在する科目のみ
    subject_list = Subject.objects.filter(exists=True).order_by('name_hiragana')

    context = {
        'subject_list': subject_list,
    }
    return render(request, 'pec/download.html', context)

def filter_exam_item_and_search(request, file_datas):
    '''
    GETのリクエストがあったとき、項目について絞り込み検索を行う
    '''
    q_exam_item = request.GET.get('filter_exam_item')
    if {'name_en': q_exam_item} in Exam_item.objects.all().values('name_en'):
        exam_item = Exam_item.objects.get(name_en=q_exam_item)
        file_datas = file_datas.filter(exam_item=exam_item)
    elif q_exam_item == 'all':
        pass
    return file_datas

def filter_existing_or_not_subject_and_search(request, subject_list):
    '''
    GETのリクエストがあったとき、授業科目について絞り込み検索を行う
    過去問があるか、ないかで科目を絞る、または全ての科目
    '''
    q_existing = request.GET.get('filter_subject')
    if q_existing == 'exists':
        subject_list = subject_list.filter(exists=True)
    elif q_existing == 'no_exists':
        subject_list = subject_list.filter(exists=False)
    else:
        pass
    return subject_list

def download_detail(request, subject_id):
    '''
    科目に対応するファイルのダウンロードページ
    '''
    # 科目のインスタンス
    subject = get_object_or_404(Subject, pk=subject_id)
    # この科目の過去問ファイル
    file_datas = subject.file_data_set.all().order_by('-year', 'exam_item')

    # 項目のリスト
    exam_item_list = Exam_item.objects.all()
    # 絞り込み検索。GETのリクエストがあったらそれに応じて絞り込み
    if 'filter_exam_item' in request.GET:
        file_datas = filter_exam_item_and_search(request, file_datas)

    # 過去問が存在する科目のみ
    subject_list = Subject.objects.filter(exists=True).order_by('name_hiragana')

    context = {
        'subject': subject,
        'subject_list': subject_list,
        'file_datas': file_datas,
        'exam_item_list': exam_item_list,
    }
    return render(request, 'pec/download_detail.html', context)

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
        wareki = 'N'+str(int(seireki)-2018) # 新しい年号は？
    return wareki

def upload_form_post(request):
    '''
    ファイルがアップロードされたときに行う処理
    viewsのuploadからよばれる
    '''
    # POST送信（ファイルがアップロードされたとき）
    context = {}
    file_uploaded = False

    if request.method == 'POST':
        error_messages = []

        # 科目
        subject = request.POST['subject']
        if subject == 'no_select':
            error_messages.append('科目を選択してください')
        elif subject == 'new_subject':
            subject = request.POST['new_subject']
            if subject == 'no_select':
                error_messages.append('科目を選択してください')

        # 年度
        year = request.POST['year']

        # 項目
        exam_item = request.POST['exam_item']
        if exam_item == 'no_select':
            error_messages.append('項目を選択してください')
        exam_item_number = int(request.POST['exam_item_number'])

        # 解答のみの如何
        only_ans = False
        if request.POST['answer'] == 'onlyans':
            only_ans = True

        # エラーがあったら処理
        if len(error_messages) != 0:
            context.update({'error_messages': error_messages})
            return context, file_uploaded

        file_form = UploadFileForm(request.POST, request.FILES)

        if file_form.is_valid():
            request_files = request.FILES['file'].name

            # ファイルの拡張子を確認
            extension = (request.FILES['file'].name).split('.',1)[1]
            extension = '.' + extension
            extension = extension.lower()
            if extension != '.pdf' and extension != '.tar':
                error_messages.append('pdfかtarファイルのみアップロードできます')
                return context, file_uploaded

            ## アップロードファイル名の確定
            file_name = subject+'-'+year+'-'+exam_item
            if exam_item_number != 0:
                file_name += str(exam_item_number)
            if only_ans:
                file_name += '^ans'
            part_of_file_name = file_name
            file_name += extension

            subject_path = os.path.join(settings.PEC_KAKOMON_ROOT, subject)
            move_to_path = os.path.join(subject_path, file_name)

            # アップロードしたいファイル名がすでにある場合は連番をつける
            # 連番: ex) mid2(3) の (3)の部分
            same_name_number = 0
            if os.path.exists(move_to_path):
                for same_name_number in range(2, 10):
                    file_name = part_of_file_name+ '('+str(same_name_number)+')'+extension
                    move_to_path = os.path.join(subject_path, file_name)
                    if os.path.exists(move_to_path):
                        continue
                    else:
                        break
                if same_name_number == 9:
                    error_messages.append('同じ名前のファイルがたくさんありますのでアップロードしませんでした。')
                    context.update({'error_messages': error_messages})
                    return context, file_uploaded

            print('move_to_path decided: ' + move_to_path)

            # 過去問がない科目だったとき、その科目のディレクトリを作成し
            # 科目インスタンスを更新する
            if os.path.exists(subject_path) == False:
                os.mkdir(subject_path)
                print('mkdir ' + subject_path)
                os.chmod(subject_path, 0o777)
                new_subject = Subject.objects.get(name_en=subject)
                print(new_subject.name_en)
                print('mkdir', subject_path)
                new_subject.exists=True
                new_subject.save()

            # 過去問ディレクトリにアップロードファイルを書き込む
            print('file upload...')
            uploaded_file = open(move_to_path, 'wb')
            while True:
                chunk = request.FILES['file'].read(1000000)
                if not chunk:
                    break
                uploaded_file.write(chunk)
            uploaded_file.close()
            os.chmod(move_to_path, 0o666)

            print('file uploaded!')
            file_uploaded = True

            ## File_dataインスタンスにアップロードされたファイルの情報を追加

            # 科目、年度、項目のインスタンスを取得
            subject_for_uploaded_file = Subject.objects.get(name_en=subject)
            year_for_uploaded_file = Year.objects.get(name_en=year)
            exam_item_for_uploaded_file = Exam_item.objects.get(name_en=exam_item)

            # アップロードファイルのサイズ
            size = os.path.getsize(move_to_path)
            unit = 'B'
            if size // 1024 != 0:
                size /= 1024
                unit = 'KB'
                if size // 1024 != 0:
                    size /= 1024
                    unit = 'MB'
            size = str(round(size, 2)) + unit # size

            # アップロードファイルの最終更新日
            dt = datetime.datetime.fromtimestamp(os.stat(move_to_path).st_mtime)
            reset_day = dt.strftime('%Y/%m/%d %H:%M:%S') # reset_day

            # File_dataの更新
            print('file_data_update...')
            File_data(
            subject=subject_for_uploaded_file,
            year=year_for_uploaded_file,
            exam_item=exam_item_for_uploaded_file,
            exam_item_number=exam_item_number,
            only_ans=only_ans,
            same_name_number=same_name_number,
            extension=extension,
            file_name=file_name,
            size=size,
            reset_day=reset_day
            ).save()

            context.update({
            'subject': subject_for_uploaded_file,
            'error_messages': error_messages,
            'file_name': file_name,
            'request_files': request_files,
            'extension': extension,
            })
            return context, file_uploaded
    else:
        return context, file_uploaded


def upload(request):
    '''
    過去問のアップロードページ
    フォームからの入力により、アップロードされたファイルの科目、年度、項目、項目に付与される番号、解答の如何、連番の情報が決定して、それにともないファイル名を変更して保存する。
    余談：
    このページの動作が欲しいためにこの過去問サイトを作成したといっても過言ではないほど重要なページである。
    '''
    context = {}
    file_uploaded = False

    ## アップロードするためのフォーム作成
    if request.method == 'POST':
        context, file_uploaded = upload_form_post(request)

    # 科目選択
    existing_subject_list = Subject.objects.filter(exists=True).order_by('name_hiragana')
    # 新しく科目追加
    new_subject_list = Subject.objects.filter(exists=False).order_by('name_hiragana')

    # 年度選択
    this_year = datetime.date.today().year
    # 今年度のYearインスタンスがなかったら作成
    seireki = str(this_year)
    wareki = get_wareki(seireki)
    obj, created =  Year.objects.get_or_create(name_en=seireki, defaults=dict(name_jp=wareki))

    # 年度リスト
    year_list = Year.objects.order_by('-name_en')

    # 項目選択
    exam_item_list = Exam_item.objects.order_by('order')
    exam_item_number = []
    for n in range(21):
        exam_item_number.append(str(n))

    file_form = UploadFileForm()
    context.update({
        'existing_subject_list': existing_subject_list,
        'new_subject_list': new_subject_list,
        'year_list': year_list,
        'exam_item_list': exam_item_list,
        'exam_item_number': exam_item_number,
        'file_form': file_form,
        'file_uploaded': file_uploaded,
    })
    return render(request, 'pec/upload.html', context)



def edit(request):
    '''
    何を編集したいか決めるページ
    * 科目名 or ファイル名
    * 項目名
    '''
    return render(request, 'pec/edit.html')

def edit_subject(request):
    '''
    何を編集したいか決めるページ
    * 科目名、ファイル名
    '''
    # どのフォームから送信するか
    which_form = ''
    # この科目のディレクトリが削除されたか
    error_messages = []
    context = {}

    # 新しく科目を追加するとき
    if 'add_form_submit_for_subject' in request.POST:
        which_form = 'add_subject'
        next_subject_name_en = request.POST['subject_name_en']
        next_subject_name_jp = request.POST['subject_name_jp']
        next_subject_name_hiragana = request.POST['subject_name_hiragana']

        # 名前の変更時に既に他で使用されている名前を使おうとしたらエラーとする
        if Subject.objects.filter(name_jp=next_subject_name_jp):
            error_messages.append('その科目名（英名）は別の科目で既に使用されております。')
        if Subject.objects.filter(name_en=next_subject_name_en):
            error_messages.append('その科目名（和名）は別の科目で既に使用されております。')
        if Subject.objects.filter(name_hiragana=next_subject_name_hiragana):
            error_messages.append('その科目名（ふりがな）は別の科目で既に使用されております。')

        # 名前の変更時に記入もれやファイル名に使用できない特殊文字があったらエラーとする
        for target in [next_subject_name_en, next_subject_name_jp, next_subject_name_hiragana]:
            if len(target) == 0:
                error_messages.append('入力されていない箇所があります')
            no_good_character_for_file_name = '-^()¥/:*?\"<>|\\'
            for c in no_good_character_for_file_name:
                if target.find(c) >= 0:
                    error_messages.append(c + ' が含まれておりました　' + no_good_character_for_file_name + '　これらの文字は利用できません')

        # エラーがあったら終了
        if len(error_messages) != 0:
            context.update({
                'error_messages': error_messages,
             })
        else:
            # 新しく科目のインスタンスを作成
            subject = Subject(
            name_en=next_subject_name_en,
            name_jp=next_subject_name_jp,
            name_hiragana=next_subject_name_hiragana,
            exists=False
            )
            subject.save()

            context.update({
                'subject': subject,
                'which_form': which_form,
                'error_messages': error_messages,
            })


    # 授業科目のリスト
    subject_list = Subject.objects.order_by('name_hiragana')

    # 絞り込み検索。GETのリクエストがあったらそれに応じて絞り込み
    if request.method == 'GET':
        subject_list = filter_existing_or_not_subject_and_search(request, subject_list)

    # 科目名変更のフォーム
    subject_add_form = SubjectForm()

    context.update({
        'subject_list': subject_list,
        'subject_add_form': subject_add_form,
    })
    return render(request, 'pec/edit_subject.html', context)

def edit_subject_detail(request, subject_id):
    '''
    科目名またはファイル名を変更、または科目、ファイルを削除できるページ
    科目名を変更したらその科目のファイル名全て変更となる
    ファイル名を変更の時、ファイルの科目名を変更したら変更した科目へ移動する
    '''

    # 科目のインスタンス
    subject = get_object_or_404(Subject, pk=subject_id)

    previous_subject_path = os.path.join(settings.PEC_KAKOMON_ROOT, subject.name_en)

    # どのフォームから送信するか
    which_form = ''
    # この科目のディレクトリが削除されたか
    error_messages = []
    context = {}

    ## POST送信による処理

    # 削除の時
    if 'delete_form_submit_for_subject' in request.POST:
        which_form = 'delete_subject'
        if os.path.exists(previous_subject_path):
            shutil.rmtree(previous_subject_path)
        subject.delete()

        # 編集する授業科目を選択する画面へ遷移
        return HttpResponseRedirect(reverse('pec:edit_subject'))

    # 科目の名前変更
    if 'rename_form_submit_for_subject' in request.POST:
        which_form = 'rename_subject'

        previous_subjcet_name_en = subject.name_en
        previous_subjcet_name_jp = subject.name_jp
        previous_subjcet_name_hiragana = subject.name_hiragana

        next_subject_name_en = request.POST['subject_name_en']
        next_subject_name_jp = request.POST['subject_name_jp']
        next_subject_name_hiragana = request.POST['subject_name_hiragana']

        # 名前の変更時に既に他で使用されている名前を使おうとしたらエラーとする
        if Subject.objects.exclude(name_jp=previous_subjcet_name_jp).filter(name_jp=next_subject_name_jp):
            error_messages.append('その科目名（英名）は別の科目で既に使用されております。')
        if Subject.objects.exclude(name_en=previous_subjcet_name_en).filter(name_en=next_subject_name_en):
            error_messages.append('その科目名（和名）は別の科目で既に使用されております。')
        if Subject.objects.exclude(name_hiragana=previous_subjcet_name_hiragana).filter(name_hiragana=next_subject_name_hiragana):
            error_messages.append('その科目名（ふりがな）は別の科目で既に使用されております。')

        # 名前の変更時に記入もれやファイル名に使用できない特殊文字があったらエラーとする
        for target in [next_subject_name_en, next_subject_name_jp, next_subject_name_hiragana]:
            if len(target) == 0:
                error_messages.append('入力されていない箇所があります')
            no_good_character_for_file_name = '-^()¥/:*?\"<>|\\'
            for c in no_good_character_for_file_name:
                if target.find(c) >= 0:
                    error_messages.append(c + ' が含まれておりました　' + no_good_character_for_file_name + '　これらの文字は利用できません')

        # エラーがあったら終了
        if len(error_messages) != 0:
            context.update({
                'error_messages': error_messages,
                'subject': subject,
                 })
        else:
        # 英名が変更されたら各ファイルのfile_nameも更新する
        # ディレクトリ及び、ファイル名も変更する
            if previous_subjcet_name_en != next_subject_name_en:
                subject.name_en = next_subject_name_en
                next_subject_path = os.path.join(settings.PEC_KAKOMON_ROOT, next_subject_name_en)
                # ディレクトリの名前を変更
                shutil.move(previous_subject_path, next_subject_path)
                print(previous_subject_path + ' -> ' + next_subject_path)
                # ファイル名の科目名の部分を変更
                for previous_file_name in os.listdir(next_subject_path):
                    # 新しいファイル名
                    next_file_name = next_subject_name_en+'-'+'-'.join(previous_file_name.split('-')[1:])
                    # 移動前のファイルのパス
                    previous_file_path = os.path.join(next_subject_path, previous_file_name)
                    # 移動後のファイルのパス
                    next_file_path = os.path.join(next_subject_path, next_file_name)
                    # 移動
                    shutil.move(previous_file_path, next_file_path)
                    print(previous_file_name + ' -> ' + next_file_name)
                    # File_dataの更新
                    file_data = File_data.objects.get(file_name=previous_file_name)
                    file_data.file_name = next_file_name
                    file_data.save()


            subject.name_jp = next_subject_name_jp
            subject.name_hiragana = next_subject_name_hiragana
            subject.save()

            context.update({
            'previous_subjcet_name_en': previous_subjcet_name_en,
            'previous_subjcet_name_jp': previous_subjcet_name_jp,
            'previous_subjcet_name_hiragana': previous_subjcet_name_hiragana,

            })

    # ファイル削除の時
    if 'delete_form_submit_for_file' in request.POST:
        pass
    # ファイルの名前の変更
    if 'delete_form_submit_for_file' in request.POST:
        pass

    # 科目名変更のフォーム
    subject_rename_form = SubjectForm(initial = {
    'subject_name_en': subject.name_en,
    'subject_name_jp': subject.name_jp,
    'subject_name_hiragana': subject.name_hiragana,
    'subject_exists': subject.exists,
    })


    # 項目のリスト
    exam_item_list = Exam_item.objects.all()

    # この科目のファイルデータ
    file_datas = subject.file_data_set.all().order_by('-year', 'exam_item')
    # 絞り込み検索。GETのリクエストがあったらそれに応じて絞り込み
    if 'filter_exam_item' in request.GET:
        file_datas = filter_exam_item_and_search(request, file_datas)

    # 科目のリスト
    subject_list = Subject.objects.all().order_by('name_hiragana')

    context.update({
        'which_form': which_form,
        'error_messages': error_messages,
        'subject': subject,
        'subject_list': subject_list,
        'file_datas': file_datas,
        'exam_item_list': exam_item_list,
        'subject_rename_form': subject_rename_form,

    })
    return render(request, 'pec/edit_subject_detail.html', context)


def edit_exam_item(request):
    '''
    項目を編集する
    項目の追加はこのページからできる
    '''
    # どのフォームから送信するか
    which_form = ''
    # この科目のディレクトリが削除されたか
    error_messages = []
    context = {}

    # 項目の追加
    if 'add_form_submit_for_exam_item' in request.POST:
        which_form = 'add_exam_item'

        next_exam_item_order = request.POST['exam_item_order']
        next_exam_item_name_en = request.POST['exam_item_name_en']
        next_exam_item_name_jp = request.POST['exam_item_name_jp']

        # 名前の変更時に既に他で使用されている名前を使おうとしたらエラーとする
        if Exam_item.objects.filter(order=next_exam_item_order):
            error_messages.append('その番号は既に使用されております。')
        if Exam_item.objects.filter(name_en=next_exam_item_name_en):
            error_messages.append('その名（和名）は既に使用されております。')
        if Exam_item.objects.filter(name_jp=next_exam_item_name_jp):
            error_messages.append('その名（英名）は既に使用されております。')

        # 名前の変更時に記入もれやファイル名に使用できない特殊文字があったらエラーとする
        for target in [next_exam_item_order, next_exam_item_name_en, next_exam_item_name_jp]:
            if len(target) == 0:
                error_messages.append('入力されていない箇所があります')
            no_good_character_for_file_name = '-^()¥/:*?\"<>|\\'
            for c in no_good_character_for_file_name:
                if target.find(c) >= 0:
                    error_messages.append(c + ' が含まれておりました　' + no_good_character_for_file_name + '　これらの文字は利用できません')

        # エラーがあったら新しい項目は作成しない
        if len(error_messages) != 0:
            context.update({
                'error_messages': error_messages,
                 })
        else:
            # 新しく項目のインスタンスを作成
            exam_item = Exam_item(
            order=next_exam_item_order,
            name_en=next_exam_item_name_en,
            name_jp=next_exam_item_name_jp
            )
            exam_item.save()

            context.update({
                'exam_item': exam_item,
                'which_form': which_form,
                'error_messages': error_messages,
            })

    # 項目のリスト
    exam_item_list = Exam_item.objects.order_by('order')

    # 項目名変更のフォーム
    exam_item_add_form = Exam_itemForm()

    context.update({
        'exam_item_list': exam_item_list,
        'exam_item_add_form': exam_item_add_form,
    })
    return render(request, 'pec/edit_exam_item.html', context)

def edit_exam_item_detail(request, exam_item_id):
    '''
    項目を編集する
    項目の追加はこのページからできる
    '''

    # 項目のインスタンス
    exam_item = get_object_or_404(Exam_item, pk=exam_item_id)
    # どのフォームから送信するか
    which_form = ''
    # この科目のディレクトリが削除されたか
    error_messages = []
    context = {}

    # 過去問のパス
    kakomon_path = settings.PEC_KAKOMON_ROOT

    # 削除の時
    if 'delete_form_submit_for_exam_item' in request.POST:
        which_form = 'delete'

        # 削除する項目をもつファイルを全て削除し、カラになったディレクトリを削除する
        for file_data in File_data.objects.all().filter(exam_item=exam_item):
            file_path = os.path.join(kakomon_path, file_data.subject.name_en, file_data.file_name)
            os.remove(file_path)
        # ディレクトリがカラになったものを削除
        for subject_name in os.listdir(kakomon_path):
            subject_path = os.path.join(kakomon_path, subject_name)
            if len(os.listdir(subject_path)) == 0:
                subject = Subject.objects.get(name_en=subject_name)
                subject.exists = False
                subject.save()
                shutil.rmtree(subject_path)
        exam_item.delete()

        # 編集する授業科目を選択する画面へ遷移
        return HttpResponseRedirect(reverse('pec:edit_exam_item'))


    # 項目の名前変更
    if 'rename_form_submit_for_exam_item' in request.POST:
        which_form = 'rename_exam_item'

        previous_exam_item_order = exam_item.order
        previous_exam_item_name_en = exam_item.name_en
        previous_exam_item_name_jp = exam_item.name_jp

        next_exam_item_order = request.POST['exam_item_order']
        next_exam_item_name_en = request.POST['exam_item_name_en']
        next_exam_item_name_jp = request.POST['exam_item_name_jp']

        # 名前の変更時に既に他で使用されている名前を使おうとしたらエラーとする
        if Exam_item.objects.exclude(order=previous_exam_item_order).filter(order=next_exam_item_order):
            error_messages.append('その番号は既に使用されております。')
        if Exam_item.objects.exclude(name_en=previous_exam_item_name_en).filter(name_jp=next_exam_item_name_jp):
            error_messages.append('その名（英名）は既に使用されております。')
        if Exam_item.objects.exclude(name_jp=previous_exam_item_name_jp).filter(name_en=next_exam_item_name_en):
            error_messages.append('その名（和名）は既に使用されております。')

        # 名前の変更時に記入もれやファイル名に使用できない特殊文字があったらエラーとする
        for target in [next_exam_item_order, next_exam_item_name_en, next_exam_item_name_jp]:
            if len(target) == 0:
                error_messages.append('入力されていない箇所があります')
            no_good_character_for_file_name = '-^()¥/:*?\"<>|\\'
            for c in no_good_character_for_file_name:
                if target.find(c) >= 0:
                    error_messages.append(c + ' が含まれておりました　' + no_good_character_for_file_name + '　これらの文字は利用できません')

        # エラーがあったら新しい項目は作成しない
        if len(error_messages) != 0:
            context.update({
                'error_messages': error_messages,
            })
        else:
            # 英名が変更されたら各ファイルのfile_nameも更新する
            # ディレクトリ及び、ファイル名も変更する
            if previous_exam_item_name_en != next_exam_item_name_en:

                file_datas = File_data.objects.filter(exam_item=exam_item)

                exam_item.name_en = next_exam_item_name_en

                # この項目の全てのファイルの名前を変更する
                for file_data in file_datas:
                    previous_file_path = os.path.join(kakomon_path, file_data.subject.name_en, file_data.file_name)

                    # 新しいファイル名
                    next_file_name = file_data.subject.name_en+'-'+file_data.year.name_en+'-'+next_exam_item_name_en
                    if file_data.exam_item_number != 0:
                        next_file_name += str(file_data.exam_item_number)
                    if file_data.only_ans:
                        next_file_name += '^ans'
                    next_file_name += file_data.extension
                    next_file_path = os.path.join(kakomon_path, file_data.subject.name_en, next_file_name)

                    # ファイルの名前変更
                    shutil.move(previous_file_path, next_file_path)
                    file_data.file_name = next_file_name
                    file_data.save()
                    print(previous_file_path + ' -> ' + next_file_path)

            exam_item.order = next_exam_item_order
            exam_item.name_jp = next_exam_item_name_jp
            exam_item.save()

            context.update({
                'which_form': which_form,
                'error_messages': error_messages,
                'previous_exam_item_order': previous_exam_item_order,
                'previous_exam_item_name_en': previous_exam_item_name_en,
                'previous_exam_item_name_jp': previous_exam_item_name_jp,
            })

    # ファイルのリスト
    file_datas = File_data.objects.filter(exam_item=exam_item)

    # 項目名変更のフォーム
    exam_item_rename_form = Exam_itemForm(initial = {
        'exam_item_order': exam_item.order,
        'exam_item_name_en': exam_item.name_en,
        'exam_item_name_jp': exam_item.name_jp,
    })

    # 項目のリスト
    exam_item_list = Exam_item.objects.all().order_by('order')

    context.update({
        'exam_item': exam_item,
        'exam_item_list': exam_item_list,
        'file_datas': file_datas,
        'exam_item_rename_form': exam_item_rename_form,
    })
    return render(request, 'pec/edit_exam_item_detail.html', context)

def edit_file_data(request):
    '''
    ファイルの一覧を表示する
    '''

    # ファイルデータ
    file_datas = File_data.objects.all().order_by('subject', '-year', 'exam_item')
    context = {
        'file_datas': file_datas,
    }
    return render(request, 'pec/edit_file_data.html', context)

def edit_file_data_detail(request, file_data_id):
    '''
    ファイルを編集する
    名前が変更されたらファイルを移動し、ファイルデータも更新する
    '''

    # ファイル
    file_data = get_object_or_404(File_data, pk=file_data_id)

    context = {}
    which_form = ''
    file_renamed = False

    # 過去問のパス
    kakomon_path = settings.PEC_KAKOMON_ROOT

    # ファイルデータを削除する
    if 'delete_form_submit_for_file_data' in request.POST:
        which_form = 'delete_form_submit_for_file_data'
        # ファイルを削除する
        file_path = os.path.join(kakomon_path, file_data.subject.name_en, file_data.file_name)
        os.remove(file_path)
        # ディレクトリがカラになっていたら削除する
        subject_path = os.path.join(kakomon_path, file_data.subject.name_en)
        subject = Subject.objects.get(name_en=file_data.subject.name_en)
        if len(os.listdir(subject_path)) == 0:
            subject.exists = False
            subject.save()
            shutil.rmtree(subject_path)
        file_data.delete()

        # 編集する授業科目を選択する画面へ遷移
        return HttpResponseRedirect(reverse('pec:edit_subject_detail', args=(subject.id,)))


    ## 名前を変更するためのフォーム作成
    if 'rename_form_submit_for_file_data' in request.POST:
        which_form = 'rename_form_submit_for_file_data'
        context, file_renamed = rename_form_post(request, file_data)

    # ファイルの前のデータ
    previous_file_data = {}
    previous_file_data['subject'] = file_data.subject
    previous_file_data['year'] = file_data.year
    previous_file_data['exam_item'] = file_data.exam_item
    previous_file_data['exam_item_number'] = file_data.exam_item_number
    previous_file_data['only_ans'] = file_data.only_ans
    previous_file_data['same_name_number'] = file_data.same_name_number
    previous_file_data['extension'] = file_data.extension
    previous_file_data['file_name'] = file_data.file_name

    # 科目選択
    existing_subject_list = Subject.objects.filter(exists=True).order_by('name_hiragana')
    # 新しく科目追加
    new_subject_list = Subject.objects.filter(exists=False).order_by('name_hiragana')

    # 年度選択
    this_year = datetime.date.today().year

    # 今年度のYearインスタンスがなかったら作成
    seireki = str(this_year)
    wareki = get_wareki(seireki)
    obj, created =  Year.objects.get_or_create(name_en=seireki, defaults=dict(name_jp=wareki))

    # 年度リスト
    year_list = Year.objects.order_by('-name_en')

    # 項目選択
    exam_item_list = Exam_item.objects.order_by('order')
    exam_item_number = []
    for n in range(21):
        exam_item_number.append(str(n))

    context.update({
        'file_data': file_data,
        'previous_file_data': previous_file_data,
        'existing_subject_list': existing_subject_list,
        'new_subject_list': new_subject_list,
        'year_list': year_list,
        'exam_item_list': exam_item_list,
        'exam_item_number': exam_item_number,
        'which_form': which_form,
        'file_renamed': file_renamed,
        'subject_list': existing_subject_list,
    })
    return render(request, 'pec/edit_file_data_detail.html', context)

def rename_form_post(request, file_data):
    '''
    ファイルの名前が変更されたときに行う処理
    viewsのedit_file_data_detailから呼び出される
    '''

    # POST送信（ファイルがアップロードされたとき）
    context = {}
    file_renamed = False

    if request.method == 'POST':
        error_messages = []

        # 科目
        subject = request.POST['subject']
        if subject == 'no_select':
            error_messages.append('科目を選択してください')
        elif subject == 'new_subject':
            subject = request.POST['new_subject']
            if subject == 'no_select':
                error_messages.append('科目を選択してください')

        # 年度
        year = request.POST['year']

        # 項目
        exam_item = request.POST['exam_item']
        if exam_item == 'no_select':
            error_messages.append('項目を選択してください')
        exam_item_number = int(request.POST['exam_item_number'])

        # 解答のみの如何
        only_ans = False
        if request.POST['answer'] == 'onlyans':
            only_ans = True

        # 拡張子
        extension = request.POST['extension']
        if extension != '.pdf' and extension != '.tar':
            error_messages.append('拡張子はpdfかtarファイルのみです')

        # エラーがあったら処理
        if len(error_messages) != 0:
            context.update({'error_messages': error_messages})
            return context, file_renamed


        ## ファイル名の確定
        file_name = subject+'-'+year+'-'+exam_item
        if exam_item_number != 0:
            file_name += str(exam_item_number)
        if only_ans:
            file_name += '^ans'
        part_of_file_name = file_name
        file_name += extension

        subject_path = os.path.join(settings.PEC_KAKOMON_ROOT, subject)
        move_to_path = os.path.join(subject_path, file_name)

        # アップロードしたいファイル名がすでにある場合は連番をつける
        # 連番: ex) mid2(3) の (3)の部分
        same_name_number = 0
        if os.path.exists(move_to_path):
            for same_name_number in range(2, 10):
                file_name = part_of_file_name+ '('+str(same_name_number)+')'+extension
                move_to_path = os.path.join(subject_path, file_name)
                if os.path.exists(move_to_path):
                    continue
                else:
                    break
            if same_name_number == 9:
                error_messages.append('同じ名前のファイルがたくさんありますのでアップロードしませんでした。')
                context.update({'error_messages': error_messages})
                return context, file_renamed
        print('move_to_path decided: ' + move_to_path)

        # 過去問がない科目だったとき、その科目のディレクトリを作成し
        # 科目インスタンスを更新する
        if os.path.exists(subject_path) == False:
            os.mkdir(subject_path)
            print('mkdir ' + subject_path)
            os.chmod(subject_path, 0o777)
            new_subject = Subject.objects.get(name_en=subject)
            print(new_subject.name_en)
            print('mkdir', subject_path)
            new_subject.exists=True
            new_subject.save()


        # ファイルの前のパス
        previous_file_path = os.path.join(settings.PEC_KAKOMON_ROOT, file_data.subject.name_en, file_data.file_name)
        # 名前の変更
        shutil.move(previous_file_path, move_to_path)
        print(previous_file_path + ' -> ' + move_to_path)
        file_renamed = True

        ## ファイルデータの更新

        # 科目、年度、項目のインスタンスを取得
        subject_for_renamed_file = Subject.objects.get(name_en=subject)
        year_for_renamed_file = Year.objects.get(name_en=year)
        exam_item_for_renamed_file = Exam_item.objects.get(name_en=exam_item)

        print('file_data_update...')
        file_data.subject = subject_for_renamed_file
        file_data.year = year_for_renamed_file
        file_data.exam_item = exam_item_for_renamed_file
        file_data.exam_item_number = exam_item_number
        file_data.only_ans = only_ans
        file_data.same_name_number = same_name_number
        file_data.extension = extension
        file_data.file_name = file_name
        file_data.save()

        context.update({
        'subject': subject_for_renamed_file,
        'file_name': file_name,
        'extension': extension,
        })
        return context, file_renamed
    else:
        return context, file_renamed
