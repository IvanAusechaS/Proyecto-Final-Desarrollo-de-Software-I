# Generated by Django 5.1.6 on 2025-03-24 19:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0006_alter_turno_descripcion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='turno',
            name='fecha_cita',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='turno',
            name='prioridad',
            field=models.CharField(choices=[('N', 'Normal'), ('P', 'Alta')], default='N', max_length=1),
        ),
    ]
