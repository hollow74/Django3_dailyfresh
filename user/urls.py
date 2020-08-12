from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls import re_path
from . import views


urlpatterns = [
    # path('register', views.register_view, name="register"),  # 注册
    # path('register_handle', views.register_handle_view, name="register_handle"),  # 注册处理

    path('register', views.RegisterView.as_view(), name='register'),  # 注册
    re_path(r'^active/(?P<token>.*)$', views.ActiveView.as_view(), name='active'),  # 激活
    path('login', views.LoginView.as_view(), name='login'),  # 登录
    path('logout', views.LogoutView.as_view(), name='logout'),  # 登出

    # path('', login_required(views.UserInfoView.as_view()), name='user'),  # 用户中心--信息页
    # path('order', login_required(views.UserOrderView.as_view()), name='order'),  # 用户中心--订单页
    # path('address', login_required(views.UserSiteView.as_view()), name='address'),  # 用户中心--地址页

    path('', views.UserInfoView.as_view(), name='user'),  # 用户中心--信息页
    re_path(r'^order/(?P<page>\d+)$', views.UserOrderView.as_view(), name='order'),  # 用户中心--订单页
    path('address', views.UserSiteView.as_view(), name='address'),  # 用户中心--地址页


]
