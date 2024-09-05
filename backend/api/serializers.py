from django.core.validators import MinValueValidator
from rest_framework import serializers

from api.fields import Base64ImageField
from recipes.models import (
    Favourite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeLink,
    Shopping,
    Tag
)
from users.models import Follow, User


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )

    def validate(self, data):
        if 'avatar' not in data:
            raise serializers.ValidationError(
                {'avatar': 'This field is required.'}
            )
        return data

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if not user.is_anonymous:
            return Follow.objects.filter(user=user, following=obj).exists()
        return False

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'password',
            'first_name',
            'last_name',
            'username'
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            username=validated_data.get('username', ''),
        )
        return user


class SimpleRecipeSerializer(serializers.ModelSerializer):
    """
    A simplified serializer to provide reduced recipe description.
    """
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class AddIngredientSerializer(serializers.ModelSerializer):
    """
    Serializer for the creation of Ingredient objects.
    """
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        validators=[MinValueValidator(
            1,
            'Minimum amount of ingredient needed'
        )]
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class AddTagSerializer(serializers.ModelSerializer):
    """
    Serializer for the creation of Ingredient objects.
    """
    id = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = Tag
        fields = ('id',)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """
    Serializer for recipe ingredients with amount for given recipe.
    """
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading Recipe objects.
    """
    author = UserSerializer()
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients',
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if not user.is_anonymous:
            return Favourite.objects.filter(recipe=obj, user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if not user.is_anonymous:
            return Shopping.objects.filter(recipe=obj, user=user).exists()
        return False


class RecipeWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for writing, updating, and deleting Recipe objects
    """
    ingredients = AddIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField(required=True, allow_null=True)
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'author'
        )

    def validate(self, data):
        if 'ingredients' not in data:
            raise serializers.ValidationError(
                {'ingredients': 'This field is required.'}
            )
        if 'tags' not in data:
            raise serializers.ValidationError(
                {'tags': 'This field is required.'}
            )
        return super().validate(data)

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'At least one ingredient is required.'
            )
        seen_ingredients = set()
        for ingredient in value:
            ingredient_id = ingredient['id']
            if ingredient_id in seen_ingredients:
                raise serializers.ValidationError(
                    f'Duplicate ingredient with ID {ingredient_id} found.'
                )
            seen_ingredients.add(ingredient_id)
        for ingredient in value:
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    'Ingredient amount must be at least 1.'
                )
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('At least one tag is required.')
        seen_tags = set()
        for tag in value:
            tag_id = tag
            if tag_id in seen_tags:
                raise serializers.ValidationError(
                    f'Duplicate tag with ID {tag_id} found.'
                )
            seen_tags.add(tag_id)
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('You have to provide an image.')
        return value

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Cooking time has to be at least 1 minute.'
            )
        return value

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = super().create(validated_data)
        self.add_tags_ingredients(ingredients, tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.ingredients.clear()
        self.add_tags_ingredients(ingredients, tags, instance)
        return super().update(instance, validated_data)

    def add_tags_ingredients(self, ingredients, tags, recipe):
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        if tags is not None:
            recipe.tags.set(tags)

    def to_representation(self, instance):
        context = self.context
        return RecipeReadSerializer(instance, context=context).data


class RecipeLinkSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        write_only=True
    )
    short_link = serializers.SerializerMethodField()

    class Meta:
        model = RecipeLink
        fields = ['recipe', 'short_link']

    def get_short_link(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/{obj.link}/')
        return obj.link

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['short-link'] = representation.pop('short_link')
        return representation


class FavouriteSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Favourite
        fields = ['id', 'user', 'recipe']
        read_only_fields = ['id', 'user']


class FollowSerializer(serializers.ModelSerializer):
    """
    Serializer for user follows.
    """
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True
    )
    following = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True
    )
    email = serializers.ReadOnlyField(source='following.email')
    id = serializers.ReadOnlyField(source='following.id')
    username = serializers.ReadOnlyField(source='following.username')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.ImageField(source='following.avatar')

    class Meta:
        model = Follow
        fields = (
            'user',
            'following',
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if not user.is_anonymous:
            return Follow.objects.filter(
                user=user,
                following=obj.following).exists()
        return False

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj.following)
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]
        serializer = SimpleRecipeSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.following).count()

    def validate(self, data):
        user = self.context['request'].user
        following = data.get('following')
        if user == following:
            raise serializers.ValidationError('You cannot follow yourself.')
        if Follow.objects.filter(user=user, following=following).exists():
            raise serializers.ValidationError(
                'You are already following this user.'
            )
        return data


class ShoppingSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
    )

    class Meta:
        model = Shopping
        fields = '__all__'
