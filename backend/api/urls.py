from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

from api.views import UserViewSet, TagViewSet, RecipeViewSet, IngredientViewSet, RecipeRedirectView
from users.authentication import LoginView, LogoutView

router_v1 = DefaultRouter()
router_v1.register('users', UserViewSet, basename='users')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')


urlpatterns = [
    path('auth/token/login/', LoginView.as_view()),
    path('auth/token/logout/', LogoutView.as_view()),
    # path('users/set_password/', ResetPasswordView.as_view()),
    path('', include('djoser.urls')),
    path('', include(router_v1.urls)),
    path('<str:link>/', RecipeRedirectView.as_view(), name='recipe-redirect'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
