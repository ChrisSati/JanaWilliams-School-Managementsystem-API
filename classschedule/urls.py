from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClassScheduleViewSet


router = DefaultRouter()
router.register(r'class-schedules', ClassScheduleViewSet, basename='classschedule')


urlpatterns = [
    path('', include(router.urls)),
]



# from django.urls import path, include
# from rest_framework.routers import DefaultRouter

# from .views import (
# ClassScheduleViewSet,
# )

# router = DefaultRouter()
# router.register(r"class-schedules", ClassScheduleViewSet, basename="classschedule")

# urlpatterns = [
#     path("api/", include(router.urls)),
# ]
