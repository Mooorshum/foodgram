from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAuthorOrStaff(BasePermission):
    """
    Custom permission to only allow authors of a recipe or staff to edit or delete it.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user == obj.author or request.user.is_staff