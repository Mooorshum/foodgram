from rest_framework import status
from rest_framework.response import Response

class AddToRelatedMixin:
    """
    Mixin to add or remove a recipe to/from a related model.
    """
    def add_to_related(self, request, model, serializer_class, add_message, remove_message):
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            related_instance, created = model.objects.get_or_create(user=user, recipe=recipe)
            if created:
                serializer = serializer_class(recipe)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response({"detail": add_message}, status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            related_instance = model.objects.filter(user=user, recipe=recipe)
            if related_instance.exists():
                related_instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({"detail": remove_message}, status=status.HTTP_400_BAD_REQUEST)