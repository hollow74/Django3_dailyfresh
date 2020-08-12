from django.urls import path
from django.urls import re_path
from . import views

urlpatterns = [
    path('index', views.IndexView.as_view(), name='index'),  # 首页
    re_path(r'^goods/(?P<goods_id>\d+)$', views.DetailView.as_view(), name='detail'),  # 详情页
    re_path(r'^list/(?P<type_id>\d+)/(?P<page>\d+)$', views.ListView.as_view(), name='list'),  # 列表页
]
