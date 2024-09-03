from rest_framework import status
from rest_framework.response import Response


class AddRemoveMixin:
    """
    Mixin to add or remove a recipe to/from a related model.
    """
    def add_or_remove(
        self,
        request,
        model,
        serializer_class,
        add_message,
        remove_message
    ):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Please login or create an account."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            instance, created = model.objects.get_or_create(
                user=user,
                recipe=recipe
            )
            if created:
                serializer = serializer_class(recipe)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {"detail": add_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif request.method == 'DELETE':
            instance = model.objects.filter(user=user, recipe=recipe)
            if instance.exists():
                instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"detail": remove_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {"detail": "Method not allowed"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
