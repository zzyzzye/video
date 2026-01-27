# Generated migration file for adding publish settings

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0008_add_video_tech_params'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='view_permission',
            field=models.CharField(
                choices=[('public', '公开'), ('private', '私密'), ('fans', '仅粉丝')],
                default='public',
                max_length=20,
                verbose_name='观看权限',
                db_index=True
            ),
            preserve_default=True,  # 确保默认值被应用
        ),
        migrations.AddField(
            model_name='video',
            name='comment_permission',
            field=models.CharField(
                choices=[('all', '允许所有人'), ('fans', '仅粉丝'), ('none', '关闭评论')],
                default='all',
                max_length=20,
                verbose_name='评论权限'
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='video',
            name='allow_download',
            field=models.BooleanField(default=False, verbose_name='允许下载'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='video',
            name='enable_danmaku',
            field=models.BooleanField(default=True, verbose_name='开启弹幕'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='video',
            name='show_in_profile',
            field=models.BooleanField(default=True, verbose_name='显示在主页'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='video',
            name='scheduled_publish_time',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='定时发布时间',
                db_index=True
            ),
        ),
        migrations.AddField(
            model_name='video',
            name='original_type',
            field=models.CharField(
                choices=[('original', '原创'), ('repost', '转载'), ('selfmade', '自制')],
                default='original',
                max_length=20,
                verbose_name='原创声明'
            ),
            preserve_default=True,
        ),
    ]
