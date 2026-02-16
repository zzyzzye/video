# Generated migration file
# 合并字段重命名和新增字段

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_service', '0002_update_moderation_field_help_text'),
    ]

    operations = [
        # 第一步：重命名旧字段
        migrations.RenameField(
            model_name='moderationresult',
            old_name='nsfw_score',
            new_name='high_score',
        ),
        migrations.RenameField(
            model_name='moderationresult',
            old_name='violence_score',
            new_name='medium_score',
        ),
        migrations.RenameField(
            model_name='moderationresult',
            old_name='sensitive_score',
            new_name='low_score',
        ),
        
        # 第二步：添加 neutral_score 字段
        migrations.AddField(
            model_name='moderationresult',
            name='neutral_score',
            field=models.FloatField(default=0.0, help_text='正常内容概率（neutral）'),
        ),
        
        # 第三步：更新字段帮助文本
        migrations.AlterField(
            model_name='moderationresult',
            name='high_score',
            field=models.FloatField(default=0.0, help_text='高风险概率（high）'),
        ),
        migrations.AlterField(
            model_name='moderationresult',
            name='medium_score',
            field=models.FloatField(default=0.0, help_text='中风险及以上累积概率（medium+）'),
        ),
        migrations.AlterField(
            model_name='moderationresult',
            name='low_score',
            field=models.FloatField(default=0.0, help_text='低风险及以上累积概率（low+）'),
        ),
    ]
