# Generated by Django 3.2.16 on 2024-09-05 16:02

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Favourite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Favourite',
                'verbose_name_plural': 'Favourites',
            },
        ),
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Ingredient name')),
                ('measurement_unit', models.CharField(choices=[('g', 'Grams'), ('kg', 'Kilograms'), ('ml', 'Milliliters'), ('L', 'Liters'), ('sps', 'Spoonfuls'), ('pcs', 'Pieces')], max_length=3, verbose_name='Measurement unit')),
            ],
            options={
                'verbose_name': 'Ingredient',
                'verbose_name_plural': 'Ingredients',
            },
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Recipe name')),
                ('image', models.ImageField(blank=True, null=True, upload_to='recipes/', verbose_name='Recipe image')),
                ('text', models.TextField(verbose_name='Recipe text')),
                ('cooking_time', models.IntegerField(verbose_name='Cooking time (in minutes)')),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='Publication date')),
            ],
            options={
                'verbose_name': 'Recipe',
                'verbose_name_plural': 'Recipes',
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='RecipeIngredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1, 'Minimum amount of ingredient needed')], verbose_name='Amount')),
            ],
            options={
                'verbose_name': 'Recipe ingredient',
                'verbose_name_plural': 'Recipe ingredients',
            },
        ),
        migrations.CreateModel(
            name='RecipeLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('link', models.CharField(blank=True, max_length=20, null=True, unique=True, verbose_name='Recipe link')),
            ],
            options={
                'verbose_name': 'Recipe link',
                'verbose_name_plural': 'Recipe links',
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Tag name')),
                ('slug', models.SlugField(blank=True, max_length=255, unique=True, verbose_name='Tag slug')),
            ],
            options={
                'verbose_name': 'Tag',
                'verbose_name_plural': 'Tags',
            },
        ),
        migrations.CreateModel(
            name='Shopping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipe', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shopping', to='recipes.recipe', verbose_name='Recipe')),
            ],
            options={
                'verbose_name': 'Shopping cart',
                'verbose_name_plural': 'Shopping carts',
            },
        ),
    ]
