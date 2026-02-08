# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0012_add_subtitles_draft'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='subtitle_style',
            field=models.JSONField(
                verbose_name='字幕样式配置',
                default=dict,
                blank=True,
                help_text='存储字幕的样式配置（颜色、字体、描边等）'
            ),
        ),
    ]
