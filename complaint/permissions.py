from rest_framework import permissions

ALLOWED_COMPLAINT_ROLES = [
    'admin', 'teacher', 'registry', 'business manager', 'vpi', 'vpa', 'dean'
]

def _norm(role):
    return (role or '').strip().lower()

class IsAllowedComplaintRole(permissions.BasePermission):
    """
    Allows create/update/delete only for configured staff roles.
    """
    def has_permission(self, request, view):
        # For non-mutating actions, fall through (IsAuthenticated will handle)
        if view.action not in ('create', 'update', 'partial_update', 'destroy'):
            return True
        return (
            request.user.is_authenticated and
            _norm(request.user.user_type) in ALLOWED_COMPLAINT_ROLES
        )

    def has_object_permission(self, request, view, obj):
        # Same as above; could refine to poster-only edit/delete if desired.
        if view.action in ('update', 'partial_update', 'destroy'):
            return (
                request.user.is_authenticated and
                _norm(request.user.user_type) in ALLOWED_COMPLAINT_ROLES
            )
        return True
