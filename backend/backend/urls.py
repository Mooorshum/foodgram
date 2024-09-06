from django.contrib import admin
from django.urls import include, path

from api.views import RecipeRedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path(
        's/<str:link>/',
        RecipeRedirectView.as_view(),
        name='recipe-redirect'
    ),
]
