from django.contrib import admin
from django.urls import path, re_path
from . import views

urlpatterns = [
    path('place', views.OrderPlaceView.as_view(), name='place'),  # 提交订单页面显示
    path('commit', views.OrderCommitView.as_view(), name='commit'),  # 创建订单
    path('pay', views.OrderPayView.as_view(), name='pay'),  # 订单支付
    path('check', views.CheckPayView.as_view(), name='check'),  # 查询交易支付情况
    re_path(r'^comment/(?P<order_id>.+)$', views.CommentView.as_view(), name='comment'),  # 订单评论
]
