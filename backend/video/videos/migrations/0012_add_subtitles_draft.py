from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0011_alter_video_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='subtitles_draft',
            field=models.JSONField(blank=True, default=list, verbose_name='字幕草稿'),
        ),
    ]
