from django.contrib import admin

# Register your models here.
from .models import Subject, Exam_item, Year, File_data


class File_dataInline(admin.TabularInline):
    model = File_data


class SubjectAdmin(admin.ModelAdmin):
    fields = ['name_en', 'name_jp', 'name_hiragana', 'exists']
    inlines = [File_dataInline]


admin.site.register(Subject, SubjectAdmin)
admin.site.register(Exam_item)
admin.site.register(Year)
admin.site.register(File_data)
