# Generated by Django 4.0.6 on 2022-08-20 03:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bluedit', '0002_alter_post_description_alter_post_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='description',
            field=models.CharField(default='hello', max_length=500),
        ),
        migrations.AlterField(
            model_name='post',
            name='image',
            field=models.URLField(default='hello'),
        ),
    ]