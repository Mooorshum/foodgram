from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework.views import APIView

from recipes.models import RecipeLink

class RecipeRedirectView(APIView):
    def get(self, request, link, *args, **kwargs):
        recipe_link = get_object_or_404(RecipeLink, link=link)
        recipe = recipe_link.recipe
        recipe_detail_url = reverse(
            'recipes-detail',
            kwargs={'pk': recipe.id}
        )
        scheme_url = request.scheme
        host_url = request.get_host()
        recipe_detail_url = recipe_detail_url.replace('/api', '')
        full_url = f"{scheme_url}://{host_url}{recipe_detail_url}"
        return HttpResponseRedirect(full_url)
