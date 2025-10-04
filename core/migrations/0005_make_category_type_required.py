# Generated manually to make category type required
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_populate_category_types'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='categories', to='core.type', verbose_name='Тип'),
        ),
    ]
