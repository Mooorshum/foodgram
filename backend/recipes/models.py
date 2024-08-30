import random
import string

from django.core.validators import MinValueValidator
from django.db import models
from users.models import User


class Tag(models.Model):
    """
    Model for recipe tags.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def __str__(self):
        return f'tag: {self.name};'


class Ingredient(models.Model):
    """
    Model for recipe ingredients.
    """
    MEASUREMENT_UNIT_CHOICES = (
        ('g', 'Grams'),
        ('kg', 'Kilograms'),
        ('ml', 'Milliliters'),
        ('l', 'liters'),
        ('spf', 'spoonfulls'),
        ('pcs', 'Pieces'),
    )
    name = models.CharField(max_length=255)
    measurement_unit = models.CharField(
        max_length=3,
        choices=MEASUREMENT_UNIT_CHOICES
    )

    def __str__(self):
        return f'{self.name}, ({self.get_measurement_unit_display()})'


class Recipe(models.Model):
    """
    Model for recipes.
    """
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    name = models.CharField(
        max_length=255,
    )
    image = models.ImageField(
        upload_to='recipes/',
        null=True,
        blank=True,
    )
    text = models.TextField()
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
    )
    cooking_time = models.IntegerField()
    pub_date = models.DateTimeField(
        verbose_name='publication_date',
        auto_now_add=True
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes'
    )

    class Meta:
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'author'],
                name='unique_recipe'
            )
        ]

    def __str__(self):
        return f'recipe: {self.name}; author: {self.author};'


class Favourite(models.Model):
    """
    Model for favourite recipes.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favourites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favourite'
            )
        ]

    def __str__(self):
        return f'user:{self.user}; recipes: {self.recipe};'


class Shopping(models.Model):
    """
    Model for recipe shopping list.
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='shopping'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recipe'
    )

    def __str__(self):
        return f'user:{self.user}; recipes: {self.recipe};'


class RecipeIngredient(models.Model):
    """
    Model to describe relation between the Recipe and Ingredient models.
    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipe',
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, 'Minimum amount of ingredient needed')],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredients'
            )
        ]


class RecipeLink(models.Model):
    """
    Model to provide shortened links to recipes.
    """
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='recipe_link'
    )
    link = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True
    )

    class Meta:
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'link'],
                name='unique_recipe_link'
            )
        ]

    def save(self, *args, **kwargs):
        if not self.link:
            self.link = self.generate_unique_link()
        super().save(*args, **kwargs)

    def generate_unique_link(self):
        length = 8
        characters = string.ascii_letters + string.digits
        while True:
            link = ''.join(random.choices(characters, k=length))
            if not RecipeLink.objects.filter(link=link).exists():
                return link
