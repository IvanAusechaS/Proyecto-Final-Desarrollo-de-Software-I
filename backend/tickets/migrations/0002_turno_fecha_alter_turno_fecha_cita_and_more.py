# Generated by Django 5.1.7 on 2025-04-03 04:03

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='turno',
            name='fecha',
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='turno',
            name='fecha_cita',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='turno',
            name='numero',
            field=models.CharField(max_length=4),
        ),
        migrations.AlterField(
            model_name='turno',
            name='prioridad',
            field=models.CharField(choices=[('N', 'Normal'), ('P', 'Prioritario')], default='N', max_length=1),
        ),
        migrations.AlterUniqueTogether(
            name='turno',
            unique_together={('punto_atencion', 'numero', 'fecha')},
        ),
    ]
