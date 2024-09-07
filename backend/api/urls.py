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

no_prefix_patterns = [
    path(
        's/<str:link>/',
        RecipeRedirectView.as_view(),
        name='recipe-redirect'
    ),
]

urlpatterns = [
    path('', include(no_prefix_patterns)),
    path('api/', include(router_v1.urls)),
    path('api/auth/token/login/', LoginView.as_view(), name='login'),
    path('api/auth/token/logout/', LogoutView.as_view(), name='logout'),
    path('api/', include('djoser.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)