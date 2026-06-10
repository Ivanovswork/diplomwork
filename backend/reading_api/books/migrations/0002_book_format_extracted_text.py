# Generated migration for EPUB support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0001_initial'),  # Убедитесь что имя зависимости правильное
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='format',
            field=models.CharField(
                choices=[('pdf', 'PDF'), ('epub', 'EPUB')],
                default='pdf',
                max_length=10,
                verbose_name='Формат'
            ),
        ),
        migrations.AddField(
            model_name='book',
            name='extracted_text',
            field=models.TextField(
                blank=True,
                null=True,
                verbose_name='Извлеченный текст'
            ),
        ),
    ]
