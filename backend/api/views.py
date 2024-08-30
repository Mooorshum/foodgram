from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum
from django.contrib.auth import update_session_auth_hash
from django_filters import rest_framework as filters
from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny


from recipes.models import Tag, Ingredient, Recipe, Favourite, Shopping, RecipeLink, RecipeIngredient
from users.models import User, Follow
from api.serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    FavouriteSerializer,
    ShoppingSerializer,
    FollowSerializer,
    RecipeLinkSerializer,
    SimpleRecipeSerializer,
)
from users.serializers import UserSerializer, UserRegistrationSerializer






class LimitPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    max_page_size = 10







class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_is_in_shopping_cart')
    author = filters.NumberFilter(field_name='author__id')
    tags = filters.ModelMultipleChoiceFilter(queryset=Tag.objects.all(), field_name='tags__slug', to_field_name='slug')

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'author', 'tags']

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and not user.is_anonymous:
            return queryset.filter(recipe__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and not user.is_anonymous:
            return queryset.filter(recipe__user=user)
        return queryset






class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = LimitPageNumberPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            permission_classes = [AllowAny]
        elif self.action in ['subscribe', 'list_subscriptions', 'reset_password', 'me', 'edit_avatar']:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]



    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'request': self.request
        })
        return context
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(response.data)
    
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        user = request.user
        if user.is_anonymous:
            return Response({"detail": "You are not authenticated."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def edit_avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response({"detail": "No avatar provided."}, status=status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                "avatar": request.build_absolute_uri(user.avatar.url)
            }, status=status.HTTP_200_OK)
        if request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribe(self, request, pk=None):
        following_user = get_object_or_404(User, pk=pk)
        user = request.user
        if request.method == 'POST':
            if user == following_user:
                return Response({"detail": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)
            if Follow.objects.filter(user=user, following=following_user).exists():
                return Response({"detail": "You are already following this user."}, status=status.HTTP_400_BAD_REQUEST)
            follow = Follow.objects.create(user=user, following=following_user)
            recipes_limit = request.query_params.get('recipes_limit')
            recipes = Recipe.objects.filter(author=following_user)
            if recipes_limit and recipes_limit.isdigit():
                recipes = recipes[:int(recipes_limit)]
            serializer = FollowSerializer(follow, context={'request': request, 'recipes': recipes})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            follow = Follow.objects.filter(user=user, following=following_user).first()
            if follow:
                follow.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({"detail": "You are not following this user."}, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['get'], url_path='subscriptions')
    def list_subscriptions(self, request):
        user = request.user
        if user.is_anonymous:
            return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)
        subscriptions = Follow.objects.filter(user=user)
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = FollowSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = FollowSerializer(subscriptions, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='set_password')
    def reset_password(self, request, *args, **kwargs):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        if not user.check_password(current_password):
            return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        return Response(status=status.HTTP_204_NO_CONTENT)





class TagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None
    permission_classes = [AllowAny,]
        







class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None








class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = LimitPageNumberPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'get_short_link']:
            permission_classes = [AllowAny] 
        elif self.action in ['create', 'partial_update', 'destroy', 'add_to_favourites', 'add_to_shopping_cart', 'download_shopping_cart']:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()
        read_serializer = RecipeReadSerializer(recipe, context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)
    
    def partial_update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if request.user == instance.author or request.user.is_staff:
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            recipe = serializer.save()
            read_serializer = RecipeReadSerializer(recipe, context={'request': request})
            return Response(read_serializer.data)
        return Response({"detail": "You are not authorized to update this recipe."}, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user == instance.author or request.user.is_staff:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "You are not authorized to delete this recipe."}, status=status.HTTP_403_FORBIDDEN)

    def perform_destroy(self, instance):
        instance.delete()

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, *args, **kwargs):
        recipe = self.get_object()
        recipe_link, created = RecipeLink.objects.get_or_create(recipe=recipe)
        serializer = RecipeLinkSerializer(recipe_link)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def add_to_favourites(self, request, *args, **kwargs):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            favorite, created = Favourite.objects.get_or_create(user=user, recipe=recipe)
            if created:
                serializer = SimpleRecipeSerializer(recipe)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response({"detail": "Recipe already in favourites."}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            favourite = Favourite.objects.filter(user=user, recipe=recipe)
            if favourite.exists():
                favourite.delete()
                serializer = SimpleRecipeSerializer(recipe)
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({"detail": "Recipe not found in favourites."}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def add_to_shopping_cart(self, request, *args, **kwargs):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            added_recipe, created = Shopping.objects.get_or_create(user=user, recipe=recipe)
            if created:
                serializer = SimpleRecipeSerializer(recipe)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response({"detail": "Recipe already in shopping cart."}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            recipe_in_cart = Shopping.objects.filter(user=user, recipe=recipe)
            if recipe_in_cart.exists():
                recipe_in_cart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({"detail": "Recipe not found in shopping cart."}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request, *args, **kwargs):
        user = request.user
        ingredients = RecipeIngredient.objects.filter(
            recipe__in=Shopping.objects.filter(user=user).values('recipe')
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        )
        shopping_list = "Shopping List:\n\n"
        for item in ingredients:
            shopping_list += f"{item['ingredient__name']}: {item['total_amount']} {item['ingredient__measurement_unit']}\n"
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response






class RecipeRedirectView(APIView):

    def get(self, request, link, *args, **kwargs):
        recipe_link = get_object_or_404(RecipeLink, link=link)
        recipe = recipe_link.recipe
        serializer = RecipeReadSerializer(recipe, context={'request': request})
        return Response(serializer.data)










class FavouriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavouriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Favourite.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        recipe_id = request.data.get('recipe_id')

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('pk')
        data = {'recipe_id': recipe_id}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"detail": "Recipe added to favorites."}, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('pk')
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return Response({"detail": "The recipe does not exist."}, status=status.HTTP_404_NOT_FOUND)

        favourite = Favourite.objects.filter(user=request.user, recipe=recipe).first()
        if favourite:
            favourite.delete()
            return Response({"detail": "Recipe removed from favorites."}, status=status.HTTP_204_NO_CONTENT)

        return Response({"detail": "This recipe was not in your favorites."}, status=status.HTTP_404_NOT_FOUND)








class ShoppingViewSet(viewsets.ModelViewSet):
    serializer_class = ShoppingSerializer
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Shopping.objects.filter(user=self.request.user)
