from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import datetime
from .models import ClassSchedule
from .serializers import ClassScheduleSerializer


# Custom permission to allow only admins or registrars to write, others read-only
class IsAdminOrRegistryOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        user = request.user
        return (
            user and user.is_authenticated and
            getattr(user, "user_type", None) in ["admin", "registry", "vpi"]
        )

# Optional base viewset if reused (not required here unless extended further)
class BaseAuthViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]


# Main viewset for ClassSchedule
class ClassScheduleViewSet(viewsets.ModelViewSet):
    queryset = ClassSchedule.objects.select_related("grade_class", "subject", "teacher").all()
    serializer_class = ClassScheduleSerializer
    permission_classes = [IsAdminOrRegistryOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["grade_class", "teacher", "day_of_week", "subject", "period"]
    search_fields = ["subject__name", "teacher__full_name", "grade_class__name"]
    ordering_fields = ["day_of_week", "period", "start_time", "end_time"]
    ordering = ["day_of_week", "period", "start_time"]

    @action(detail=False, methods=["get"], url_path="today")
    def today_schedule(self, request):
        today = datetime.today().isoweekday()  # Monday = 1
        queryset = self.filter_queryset(
            self.queryset.filter(day_of_week=today)
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="by-teacher")
    def by_teacher(self, request):
        teacher_id = request.query_params.get("teacher_id")
        if not teacher_id:
            return Response({"error": "teacher_id query parameter is required"}, status=400)
        queryset = self.filter_queryset(
            self.queryset.filter(teacher_id=teacher_id)
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="by-class")
    def by_class(self, request):
        grade_class_id = request.query_params.get("grade_class_id")
        if not grade_class_id:
            return Response({"error": "grade_class_id query parameter is required"}, status=400)
        queryset = self.filter_queryset(
            self.queryset.filter(grade_class_id=grade_class_id)
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="by-day")
    def by_day(self, request):
        day = request.query_params.get("day")  # expects 1-5 (Mon–Fri)
        if not day:
            return Response({"error": "day query parameter is required"}, status=400)
        queryset = self.filter_queryset(
            self.queryset.filter(day_of_week=day)
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
 