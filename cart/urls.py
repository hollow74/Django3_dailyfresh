from django.contrib import admin
from django.urls import path
from django.urls import re_path
from . import views

urlpatterns = [
    path('add', views.CartAddView.as_view(), name='add'),  # 购物车记录添加
    path('', views.CartInfoView.as_view(), name='show'),  # 购物车页面显示
    path('update', views.CartUpdateView.as_view(), name='update'),  # 购物车记录更新
    path('delete', views.CartDeleteView.as_view(), name='delete'),  # 购物车记录删除

]
