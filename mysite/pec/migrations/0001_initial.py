# Generated by Django 2.0.4 on 2018-06-15 10:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Exam_item',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField()),
                ('name_en', models.CharField(max_length=80)),
                ('name_jp', models.CharField(max_length=80)),
            ],
        ),
        migrations.CreateModel(
            name='File_data',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exam_item_number', models.IntegerField(default=0)),
                ('only_ans', models.BooleanField(default=False)),
                ('same_name_number', models.IntegerField(default=0)),
                ('extension', models.CharField(max_length=20)),
                ('file_name', models.CharField(max_length=80)),
                ('size', models.CharField(max_length=80)),
                ('reset_day', models.CharField(max_length=80)),
                ('exam_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pec.Exam_item')),
            ],
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_en', models.CharField(max_length=80)),
                ('name_jp', models.CharField(max_length=80)),
                ('name_hiragana', models.CharField(max_length=80)),
                ('exists', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Year',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_en', models.CharField(max_length=80)),
                ('name_jp', models.CharField(max_length=80)),
            ],
        ),
        migrations.AddField(
            model_name='file_data',
            name='subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pec.Subject'),
        ),
        migrations.AddField(
            model_name='file_data',
            name='year',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pec.Year'),
        ),
    ]
