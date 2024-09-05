from django.contrib.auth import update_session_auth_hash
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.filters import RecipeFilter
from api.mixins import AddRemoveMixin
from api.pagination import LimitPageNumberPagination
from api.permissions import IsAuthorOrStaffOrReadOnly
from api.serializers import (
    FavouriteSerializer,
    FollowSerializer,
    IngredientSerializer,
    RecipeLinkSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShoppingSerializer,
    SimpleRecipeSerializer,
    TagSerializer,
    UserRegistrationSerializer,
    UserSerializer
)
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


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = LimitPageNumberPagination

    def get_permissions(self):
        permission_classes = []
        if self.action in ['list', 'retrieve', 'create']:
            permission_classes = [AllowAny]
        elif self.action in [
            'subscribe',
            'list_subscriptions',
            'reset_password',
            'me',
            'edit_avatar'
        ]:
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

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def edit_avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = self.get_serializer(
                user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                "avatar": request.build_absolute_uri(user.avatar.url)
            }, status=status.HTTP_200_OK)
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribe(self, request, pk=None):
        following_user = get_object_or_404(User, pk=pk)
        user = request.user
        if request.method == 'POST':
            if user == following_user:
                return Response(
                    {"detail": "You cannot follow yourself."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Follow.objects.filter(
                user=user,
                following=following_user
            ).exists():
                return Response(
                    {"detail": "You are already following this user."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow = Follow.objects.create(user=user, following=following_user)
            serializer = FollowSerializer(
                follow,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        follow = Follow.objects.filter(
            user=user,
            following=following_user
        ).first()
        if follow:
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": "You are not following this user."},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'], url_path='subscriptions')
    def list_subscriptions(self, request):
        user = request.user
        subscriptions = Follow.objects.filter(user=user).order_by('-id')
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = FollowSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = FollowSerializer(
            subscriptions,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='set_password')
    def reset_password(self, request, *args, **kwargs):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        if not user.check_password(current_password):
            return Response(
                {'error': 'Current password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None
    permission_classes = [AllowAny]


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet, AddRemoveMixin):
    queryset = Recipe.objects.all()
    pagination_class = LimitPageNumberPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'get_short_link']:
            permission_classes = [AllowAny]
        elif self.action in [
            'create', 'add_to_delete_from_favourites',
            'add_to_delete_from_shopping_cart', 'download_shopping_cart'
        ]:
            permission_classes = [IsAuthenticated]
        elif self.action in ['partial_update', 'destroy']:
            permission_classes = [IsAuthorOrStaffOrReadOnly]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, *args, **kwargs):
        recipe = self.get_object()
        recipe_link, _ = RecipeLink.objects.get_or_create(recipe=recipe)
        serializer = RecipeLinkSerializer(
            recipe_link,
            context={'request': request}
        )
        short_link = serializer.data.get('short-link', '')
        if short_link:
            pyperclip.copy(short_link)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True, methods=['post', 'delete'],
        url_path='favorite', permission_classes=[IsAuthenticated]
    )
    def add_to_delete_from_favourites(self, request, *args, **kwargs):
        return self.add_or_remove(
            request,
            model=Favourite,
            serializer_class=SimpleRecipeSerializer,
            add_message="Recipe already in favourites.",
            remove_message="Recipe not found in favourites."
        )

    @action(
        detail=True, methods=['post', 'delete'],
        url_path='shopping_cart', permission_classes=[IsAuthenticated]
    )
    def add_to_delete_from_shopping_cart(self, request, *args, **kwargs):
        return self.add_or_remove(
            request,
            model=Shopping,
            serializer_class=SimpleRecipeSerializer,
            add_message="Recipe already in shopping cart.",
            remove_message="Recipe not found in shopping cart."
        )

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
            shopping_list += (
                f"{item['ingredient__name']}: "
                f"{item['total_amount']} "
                f"{item['ingredient__measurement_unit']}\n"
            )
        response = HttpResponse(shopping_list, content_type='text/plain')
        response[
            'Content-Disposition'
        ] = 'attachment; filename="shopping_list.txt"'
        return response


class RecipeRedirectView(APIView):

    def get(self, request, link, *args, **kwargs):
        recipe_link = get_object_or_404(RecipeLink, link=link)
        recipe = recipe_link.recipe
        return redirect('recipe-detail', pk=recipe.pk)


class FavouriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavouriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Favourite.objects.filter(user=self.request.user)


class ShoppingViewSet(viewsets.ModelViewSet):
    serializer_class = ShoppingSerializer
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Shopping.objects.filter(user=self.request.user)
