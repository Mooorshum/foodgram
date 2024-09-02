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
        verbose_name='tag name',
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        verbose_name='tag slug',
    )
    
    class Meta:
        verbose_name = "tag"
        verbose_name_plural = "tags"

    def __str__(self):
        return f'tag: {self.name};'


class Ingredient(models.Model):
    """
    Model for recipe ingredients.
    """
    GRAMS = 'g'
    KILOGRAMS = 'mg'
    MILLILITERS = 'ml'
    LITERS = 'L'
    SPOONFULLS = 'sps'
    PIECES = 'pcs'
    MEASUREMENT_UNIT_CHOICES = (
        (GRAMS, 'Grams'),
        (KILOGRAMS, 'Kilograms'),
        (MILLILITERS, 'Milliliters'),
        (LITERS, 'liters'),
        (SPOONFULLS, 'spoonfulls'),
        (PIECES, 'Pieces'),
    )
    name = models.CharField(
        max_length=255,
        verbose_name='ingredient name',
    )
    measurement_unit = models.CharField(
        max_length=3,
        choices=MEASUREMENT_UNIT_CHOICES,
        verbose_name='ingredient measurment unit',
    )
    
    class Meta:
        verbose_name = "ingredient"
        verbose_name_plural = "ingredients"

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
        verbose_name='recipe author',
    )
    name = models.CharField(
        max_length=255,
        verbose_name='recipe name',
    )
    image = models.ImageField(
        upload_to='recipes/',
        null=True,
        blank=True,
        verbose_name='recipe image',
    )
    text = models.TextField(
        verbose_name='recipe text',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='recipe ingredients',
    )
    cooking_time = models.IntegerField()
    pub_date = models.DateTimeField(
        verbose_name='publication date',
        auto_now_add=True,
        verbose_name='recipe publication date',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='recipe tag',
        related_name='recipes',
        verbose_name='recipe tags',
    )

    class Meta:
        verbose_name = "recipe"
        verbose_name_plural = "recipes"
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
        related_name='favourites',
        verbose_name='favouriting user',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='favourited recipe',
    )

    class Meta:
        verbose_name = "favourite"
        verbose_name_plural = "favourites"
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
        related_name='shopping',
        verbose_name='shopping cart user',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recipe',
        verbose_name='shopping cart recipe',
    )

    class Meta:
        verbose_name = "shopping cart"
        verbose_name_plural = "shopping carts"
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                name='unique_user'
            )
        ]

    def __str__(self):
        return f'user:{self.user}; recipes: {self.recipe};'


class RecipeIngredient(models.Model):
    """
    Model to describe relation between the Recipe and Ingredient models.
    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='recipe',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipe',
        verbose_name='ingredient',
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, 'Minimum amount of ingredient needed')],
        verbose_name='amount',
    )

    class Meta:
        verbose_name = "recipe ingredient"
        verbose_name_plural = "recipe ingredients"
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
        verbose_name = "linked recipe"
    )
    link = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name = "recipe link",
    )

    class Meta:
        verbose_name = "recipe link"
        verbose_name_plural = "recipe links"
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
