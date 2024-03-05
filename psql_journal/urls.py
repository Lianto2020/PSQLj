from django.urls import path

from . import views

app_name = "psqlj"
urlpatterns = [
    path(""     , views.index,                          name="index"),
    path("add/" , views.TwoInputCreateView.as_view(),   name="add"),
    path("madd/", views.TwoInputMultipleCreateView.as_view(), 
        name="multiple-add"),
    path("list/", views.TwoInputListView.as_view(),     name="list"),

    path("tested1/", views.MainFormView.as_view(),   name="tested1"),
    path("test2/", views.MasterCreateView.as_view(), name="test2"),
]


