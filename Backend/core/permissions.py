from rest_framework.permissions import BasePermission

class IsMessOwner(BasePermission):
    """
    Permission for mess owners only
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'mess_owner'
        )

class IsCustomer(BasePermission):
    """
    Permission for customers (student or regular)
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type in ['student', 'regular']
        )

class IsMessOwnerOrReadOnly(BasePermission):
    """
    Permission for mess owners with write access, others read-only
    """
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user.is_authenticated
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'mess_owner'
        )
