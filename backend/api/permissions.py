from rest_framework import permissions


class IsAuthorOrAdminOrReadOnly(permissions.BasePermission):
    """
    Unauthorized user are only allowed to perform GET requests.
    Object authors and admins are allowed to perfom all other kinds of requests.
    """
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (obj.author == request.user
                or request.user.is_superuser)
