# Generated migration file

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0014_videoreport'),
    ]

    operations = [
        migrations.AlterField(
            model_name='video',
            name='status',
            field=models.CharField(
                choices=[
                    ('uploading', '上传中'),
                    ('pending_subtitle_edit', '等待字幕编辑'),
                    ('processing', '处理中'),
                    ('ready', '就绪'),
                    ('failed', '失败'),
                    ('pending', '待审核'),
                    ('approved', '已通过'),
                    ('rejected', '已拒绝'),
                    ('taken_down', '已下架'),
                ],
                db_index=True,
                default='uploading',
                max_length=30,
                verbose_name='状态'
            ),
        ),
        migrations.AddField(
            model_name='video',
            name='taken_down_reason',
            field=models.TextField(blank=True, verbose_name='下架原因'),
        ),
        migrations.AddField(
            model_name='video',
            name='taken_down_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='下架时间'),
        ),
    ]
