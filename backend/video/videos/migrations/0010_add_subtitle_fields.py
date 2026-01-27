# Generated migration for subtitle detection fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0009_add_publish_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='has_subtitle',
            field=models.BooleanField(db_index=True, default=False, verbose_name='是否有字幕'),
        ),
        migrations.AddField(
            model_name='video',
            name='subtitle_type',
            field=models.CharField(
                choices=[('none', '无字幕'), ('soft', '软字幕'), ('hard', '硬字幕')],
                default='none',
                max_length=20,
                verbose_name='字幕类型'
            ),
        ),
        migrations.AddField(
            model_name='video',
            name='subtitle_language',
            field=models.CharField(blank=True, max_length=50, verbose_name='字幕语言'),
        ),
        migrations.AddField(
            model_name='video',
            name='subtitle_detected_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='字幕检测时间'),
        ),
    ]
