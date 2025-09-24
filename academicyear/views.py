from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import AcademicYear

class AcademicYearListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        years = AcademicYear.objects.all().order_by('-start_date')
        data = [{"id": y.id, "name": y.name, "is_active": y.is_active} for y in years]
        return Response(data)





class ActiveAcademicYearView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            active_year = AcademicYear.objects.get(is_active=True)
            data = {
                "id": active_year.id,
                "name": active_year.name,
                "is_active": active_year.is_active,
                "start_date": active_year.start_date,
                "end_date": active_year.end_date
            }
            return Response(data)
        except AcademicYear.DoesNotExist:
            return Response({"detail": "No active academic year found"}, status=404)
