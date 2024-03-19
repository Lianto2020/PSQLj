from django.urls import path

from . import views

app_name = "psqlj"
urlpatterns = [
#    path("", views.index, name="index"),

    path("", views.MasterCreateView.as_view(), name="index"),
]


