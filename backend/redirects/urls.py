from django.urls import path
from redirects.views import RecipeRedirectView

urlpatterns = [
    path('s/<str:link>/', RecipeRedirectView.as_view(), name='recipe-redirect'),
]
