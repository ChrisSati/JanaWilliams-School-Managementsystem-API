from rest_framework import permissions

class IsOwnGrade(permissions.BasePermission):
    """
    Custom permission to allow a student to view only their own grades.
    """

    def has_object_permission(self, request, view, obj):
        # Only allow access if the student is the same as the logged-in user
        return obj.student == request.user.student
