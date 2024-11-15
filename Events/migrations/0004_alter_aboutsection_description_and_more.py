# Generated by Django 5.1.3 on 2024-11-14 09:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Events', '0003_alter_aboutsection_description_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aboutsection',
            name='description',
            field=models.TextField(help_text='Enter the main description (use paragraphs separated by \\n)', verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='aboutsection',
            name='subtitle',
            field=models.CharField(help_text='Enter a subtitle for the about section', max_length=255, verbose_name='Subtitle'),
        ),
        migrations.AlterField(
            model_name='stat',
            name='number',
            field=models.CharField(help_text='Enter the statistic number (e.g., 300+)', max_length=50, verbose_name='Statistic Number'),
        ),
        migrations.AlterField(
            model_name='stat',
            name='text',
            field=models.CharField(help_text='Enter the statistic description', max_length=100, verbose_name='Statistic Description'),
        ),
    ]
