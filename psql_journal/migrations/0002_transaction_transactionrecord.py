# Generated by Django 4.2.4 on 2024-02-22 23:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('psql_journal', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tdate', models.DateField()),
                ('desc', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='TransactionRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('record_num', models.SmallIntegerField()),
                ('account', models.CharField(max_length=200)),
                ('amount', models.PositiveBigIntegerField()),
                ('transaction', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='psql_journal.transaction')),
            ],
        ),
    ]
