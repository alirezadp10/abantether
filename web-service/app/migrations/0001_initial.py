# Generated by Django 3.2 on 2025-02-20 23:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CryptoCurrency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=10, unique=True)),
                ('name', models.CharField(db_index=True, max_length=50)),
                ('price', models.DecimalField(decimal_places=8, max_digits=18)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'app.crypto_currency',
            },
        ),
        migrations.CreateModel(
            name='Exchanger',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('api_url', models.URLField()),
                ('fee_percentage', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'app.exchanger',
            },
        ),
        migrations.CreateModel(
            name='ExchangeTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], default='Pending', max_length=10)),
                ('amount', models.DecimalField(decimal_places=8, max_digits=18)),
                ('try_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('exchanger', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='app.exchanger')),
            ],
            options={
                'db_table': 'app.exchange_transaction',
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=8, max_digits=18)),
                ('count', models.PositiveSmallIntegerField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('canceled', 'Canceled')], default='Pending', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('crypto_currency', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='app.cryptocurrency')),
            ],
            options={
                'db_table': 'app.order',
            },
        ),
        migrations.CreateModel(
            name='UserWallet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.DecimalField(decimal_places=8, default=0, max_digits=18)),
                ('locked_balance', models.DecimalField(decimal_places=8, default=0, max_digits=18)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'app.user_wallet',
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=8, max_digits=18)),
                ('type', models.CharField(choices=[('credit', 'Credit'), ('debit', 'Debit')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'app.transaction',
            },
        ),
        migrations.CreateModel(
            name='OrderExchangeTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('exchange_transaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.exchangetransaction')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.order')),
            ],
            options={
                'db_table': 'app.order_exchange_transaction',
            },
        ),
        migrations.AddField(
            model_name='order',
            name='exchange_transaction',
            field=models.ManyToManyField(related_name='exchange_transactions', through='app.OrderExchangeTransaction', to='app.ExchangeTransaction'),
        ),
        migrations.AddField(
            model_name='order',
            name='transaction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='app.transaction'),
        ),
        migrations.AddField(
            model_name='order',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='exchangetransaction',
            name='order',
            field=models.ManyToManyField(related_name='orders', through='app.OrderExchangeTransaction', to='app.Order'),
        ),
        migrations.CreateModel(
            name='ExchangerRequestLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request', models.TextField()),
                ('response', models.TextField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('exchange_transaction', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='app.exchangetransaction')),
            ],
            options={
                'db_table': 'app.exchanger_request_log',
            },
        ),
    ]
