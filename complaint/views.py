from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Complaint
from .serializers import ComplaintSerializer
from .permissions import IsAllowedComplaintRole, ALLOWED_COMPLAINT_ROLES

from notifications.models import Notification  # your existing Notification model


class ComplaintViewSet(viewsets.ModelViewSet):
    """
    CRUD for student complaints.

    - Staff roles (allowed) can create, edit, delete.
    - Parents see only complaints about their linked students.
    - Others see none.
    """
    serializer_class = ComplaintSerializer
    permission_classes = [permissions.IsAuthenticated, IsAllowedComplaintRole]

    def get_queryset(self):
        user = self.request.user
        role = (user.user_type or '').lower()

        if role == 'parent':
            # Only complaints about children linked to this parent
            return Complaint.objects.filter(student__parent=user).select_related('student', 'poster')

        if role in ALLOWED_COMPLAINT_ROLES:
            # Staff can see all (adjust if you want to restrict to same division, etc.)
            return Complaint.objects.all().select_related('student', 'poster')

        # Students & others see nothing
        return Complaint.objects.none()

    def perform_create(self, serializer):
        """
        Save complaint & trigger notification to parent.
        """
        complaint = serializer.save(poster=self.request.user)

        parent = getattr(complaint.student, 'parent', None)
        if parent:
            Notification.objects.create(
                user=parent,
                title="Student Complaint",
                message=f"A new complaint has been posted for {complaint.student.full_name}: {complaint.title}",
                type="general",
                url=None  # optionally link to your frontend path
            )

    # Optional helper endpoint: mark complaint-related notifications as read
    @action(methods=['post'], detail=True, url_path='mark-parent-notifications-read',
            permission_classes=[permissions.IsAuthenticated])
    def mark_parent_notifications_read(self, request, pk=None):
        complaint = self.get_object()
        parent = getattr(complaint.student, 'parent', None)
        if not parent or request.user != parent:
            return Response(status=status.HTTP_403_FORBIDDEN)

        Notification.objects.filter(
            user=parent,
            title="Student Complaint",
            message__icontains=complaint.title
        ).update(is_read=True)
        return Response({"status": "ok"})
