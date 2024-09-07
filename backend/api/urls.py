from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    IngredientViewSet,
    RecipeRedirectView,
    RecipeViewSet,
    TagViewSet,
    UserViewSet
)

from users.authentication import LoginView, LogoutView

router_v1 = DefaultRouter()
router_v1.register('users', UserViewSet, basename='users')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [

    path('', include(router_v1.urls)),
    path('auth/token/login/', LoginView.as_view(), name='login'),
    path('auth/token/logout/', LogoutView.as_view(), name='logout'),
    path('', include('djoser.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
