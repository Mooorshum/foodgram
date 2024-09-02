import random
import string

from django.core.validators import MinValueValidator
from django.db import models

from users.models import User


class Tag(models.Model):
    """
    Model for recipe tags.
    """
    name = models.CharField(
        max_length=255,
        verbose_name='Tag name',
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        verbose_name='Tag slug',
    )
    
    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return f'Tag: {self.name};'


class Ingredient(models.Model):
    """
    Model for recipe ingredients.
    """
    GRAMS = 'g'
    KILOGRAMS = 'kg'
    MILLILITERS = 'ml'
    LITERS = 'L'
    SPOONFULLS = 'sps'
    PIECES = 'pcs'
    MEASUREMENT_UNIT_CHOICES = (
        (GRAMS, 'Grams'),
        (KILOGRAMS, 'Kilograms'),
        (MILLILITERS, 'Milliliters'),
        (LITERS, 'Liters'),
        (SPOONFULLS, 'Spoonfuls'),
        (PIECES, 'Pieces'),
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Ingredient name',
    )
    measurement_unit = models.CharField(
        max_length=3,
        choices=MEASUREMENT_UNIT_CHOICES,
        verbose_name='Measurement unit',
    )
    
    class Meta:
        verbose_name = "Ingredient"
        verbose_name_plural = "Ingredients"

    def __str__(self):
        return f'{self.name}, ({self.get_measurement_unit_display()})'


class Recipe(models.Model):
    """
    Model for recipes.
    """
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Author',
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Recipe name',
    )
    image = models.ImageField(
        upload_to='recipes/',
        null=True,
        blank=True,
        verbose_name='Recipe image',
    )
    text = models.TextField(
        verbose_name='Recipe text',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ingredients',
    )
    cooking_time = models.IntegerField(
        verbose_name='Cooking time (in minutes)',
    )
    pub_date = models.DateTimeField(
        verbose_name='Publication date',
        auto_now_add=True,
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Tags',
        related_name='recipes',
    )

    class Meta:
        verbose_name = "Recipe"
        verbose_name_plural = "Recipes"
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'author'],
                name='unique_recipe'
            )
        ]

    def __str__(self):
        return f'Recipe: {self.name}; Author: {self.author};'


class Favourite(models.Model):
    """
    Model for favourite recipes.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favourites',
        verbose_name='User',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Recipe',
    )

    class Meta:
        verbose_name = "Favourite"
        verbose_name_plural = "Favourites"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favourite'
            )
        ]

    def __str__(self):
        return f'User: {self.user}; Recipe: {self.recipe};'


class Shopping(models.Model):
    """
    Model for recipe shopping list.
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='shopping',
        verbose_name='User',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shopping',
        verbose_name='Recipe',
    )

    class Meta:
        verbose_name = "Shopping cart"
        verbose_name_plural = "Shopping carts"
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                name='unique_user'
            )
        ]

    def __str__(self):
        return f'User: {self.user}; Recipe: {self.recipe};'


class RecipeIngredient(models.Model):
    """
    Model to describe relation between the Recipe and Ingredient models.
    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Recipe',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipe',
        verbose_name='Ingredient',
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, 'Minimum amount of ingredient needed')],
        verbose_name='Amount',
    )

    class Meta:
        verbose_name = "Recipe ingredient"
        verbose_name_plural = "Recipe ingredients"
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
        related_name='recipe_link',
        verbose_name='Linked recipe'
    )
    link = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Recipe link',
    )

    class Meta:
        verbose_name = "Recipe link"
        verbose_name_plural = "Recipe links"
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
