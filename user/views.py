from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.mail import send_mail
from django.views import View
from django.conf import settings
from django_redis import get_redis_connection
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.http import HttpResponse
from django.http import HttpResponseRedirect
import re
from order.models import OrderInfo, OrderGoods
from goods.models import GoodsSKU
from utils.mixin import LoginRequiredMixin
from . import models
from celery_tasks.tasks import send_register_active_email


# Create your views here.

# /user/register
def register_view(request):
    """注册"""
    if request.method == 'GET':
        """显示注册页面"""
        return render(request, 'user/register.html')
    elif request.method == 'POST':
        """显示注册处理"""
        # 接收数据
        username = request.POST.get('user_name')
        pwd = request.POST.get('pwd')
        # cpwd = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 进行数据校验
        if not all([username, pwd, email]):
            # 数据不完整
            return render(request, 'user/register.html', {'errmsg': '数据不完整'})

        # 邮箱校验
        if not re.match(r'^[a-zA-Z0-9][\w.\-]*@[a-zA-Z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'user/register.html', {'errmsg': '邮箱不合法'})

        if allow != 'on':
            return render(request, 'user/register.html', {'errmsg': '请同意协议'})

        # 校验用户名是否重复
        try:
            user = models.User.objects.get(username=username)
        except models.User.DoesNotExist:
            # 用户名不存在
            user = None
        if user:
            # 用户名已存在
            return render(request, 'user/register.html', {'errmsg': '用户名已存在'})

        # 进行业务处理：进行用户注册
        # user = models.User.objects.create(username=username, password=pwd, email=email)
        # 创建user最直接的方法create_user()辅助函数
        user = models.User.objects.create_user(username, email, pwd)
        user.is_active = 0
        user.save()

        # 返回应答,跳转到首页(使用反向解析)
        return redirect(reverse("index"))


# /user/register_handle
def register_handle_view(request):
    """显示注册处理"""
    # 接收数据
    username = request.POST.get('user_name')
    pwd = request.POST.get('pwd')
    # cpwd = request.POST.get('cpwd')
    email = request.POST.get('email')
    allow = request.POST.get('allow')
    # 进行数据校验
    if not all([username, pwd, email]):
        # 数据不完整
        return render(request, 'user/register.html', {'errmsg': '数据不完整'})

    # 邮箱校验
    if not re.match(r'^[a-zA-Z0-9][\w.\-]*@[a-zA-Z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'user/register.html', {'errmsg': '邮箱不合法'})

    if allow != 'on':
        return render(request, 'user/register.html', {'errmsg': '请同意协议'})

    # 校验用户名是否重复
    try:
        user = models.User.objects.get(username=username)
    except models.User.DoesNotExist:
        # 用户名不存在
        user = None
    if user:
        # 用户名已存在
        return render(request, 'user/register.html', {'errmsg': '用户名已存在'})

    # 进行业务处理：进行用户注册
    # user = models.User.objects.create(username=username, password=pwd, email=email)
    # 创建user最直接的方法create_user()辅助函数
    user = models.User.objects.create_user(username, email, pwd)
    user.is_active = 0
    user.save()

    # 返回应答,跳转到首页(使用反向解析)
    return redirect(reverse("index"))


# /user/register
class RegisterView(View):
    """注册"""

    def get(self, request):
        """显示注册页面"""
        return render(request, 'user/register.html')

    def post(self, request):
        """显示注册处理"""
        # 接收数据
        username = request.POST.get('user_name')
        pwd = request.POST.get('pwd')
        # cpwd = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 进行数据校验
        if not all([username, pwd, email]):
            # 数据不完整
            return render(request, 'user/register.html', {'errmsg': '数据不完整'})

        # 邮箱校验
        if not re.match(r'^[a-zA-Z0-9][\w.\-]*@[a-zA-Z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'user/register.html', {'errmsg': '邮箱不合法'})

        if allow != 'on':
            return render(request, 'user/register.html', {'errmsg': '请同意协议'})

        # 校验用户名是否重复
        try:
            user = models.User.objects.get(username=username)
        except models.User.DoesNotExist:
            # 用户名不存在
            user = None
        if user:
            # 用户名已存在
            return render(request, 'user/register.html', {'errmsg': '用户名已存在'})

        # 进行业务处理：进行用户注册
        # user = models.User.objects.create(username=username, password=pwd, email=email)
        # 创建user最直接的方法create_user()辅助函数
        user = models.User.objects.create_user(username, email, pwd)
        user.is_active = 0
        user.save()

        # 发送激活邮件，包含激活链接: http://127.0.0.1:8000/user/active/1
        # 激活链接中需要包含用户的身份信息，并且要对信息加密

        # 加密用户的身份信息，生成激活token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)  # byte
        token = token.decode()

        # 发邮件
        send_register_active_email.delay(email, username, token)

        # 返回应答,跳转到首页(使用反向解析)
        return redirect(reverse('index'))


class ActiveView(View):
    """用户激活"""

    def get(self, request, token):
        """进行用户激活"""
        # 进行解密，获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 获取待激活用户的id
            user_id = info['confirm']

            # 根据id获取用户信息
            user = models.User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 跳转到登录页面
            return HttpResponseRedirect('/user/login')  # 路由
        except SignatureExpired as e:
            # 激活链接已过期
            return HttpResponse('激活链接已过期')


# /user/login
class LoginView(View):
    """登录"""

    def get(self, request):
        """显示登录页面"""
        # 判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        # 使用模板
        return render(request, 'user/login.html', locals())

    def post(self, request):
        """登录校验"""
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        # 校验数据
        if not all([username, password]):
            # 数据不完整
            return render(request, 'user/login.html', {'errmsg': '数据不完整'})

        # 业务处理:登录校验
        # models.User.objects.get(username=username, password=password)
        # django内置的登录校验 ---- authenticate
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # 用户名密码正确
            if user.is_active:
                # 用户已激活
                # 记录用户的登录状态
                login(request, user)

                # 获取登录后所要跳转到的地址
                # 默认跳转到首页
                next_url = request.GET.get('next', reverse('index'))

                # 判断是否需要记住用户名
                remember = request.POST.get('remember')

                # 跳转到next_url
                response = HttpResponseRedirect(next_url)

                if remember == 'on':
                    # 记住用户名
                    response.set_cookie('username', username, max_age=7 * 24 * 3600)
                else:
                    response.delete_cookie('username')

                # 返回response
                return response

            else:
                # 用户未激活
                return render(request, 'user/login.html', {'errmsg': '账户未激活'})
        else:
            # 用户名或密码错误
            return render(request, 'user/login.html', {'errmsg': '用户名或密码错误'})


# user/logout
class LogoutView(View):
    """退出登录"""
    def get(self, request):
        # 清除用户的session信息
        logout(request)

        # 跳转到首页
        return redirect(reverse('index'))


# /user
class UserInfoView(LoginRequiredMixin, View):
    """用户中心信息页"""

    def get(self, request):
        """显示"""
        page = 'user'
        # 请求过来之后，django框架本身会给request对象增加一个user属性request.user
        # 如果用户未登录->user是AnonymousUser类的一个实例对象
        # 如果用户登录->user是User类的一个实例对象
        # request.user.is_authenticated()

        # 获取用户的个人信息
        user = request.user
        address = models.Address.objects.get_default_address(user)

        # 获取用户的历史浏览记录
        # import redis
        # r = redis.Redis(host='127.0.0.1', port='6379', db=2)
        con = get_redis_connection('default')

        history_key = 'history_%d' % user.id

        # 获取用户最新浏览的5个商品的id
        sku_ids = con.lrange(history_key, 0, 4)  # [2, 3, 1]

        # 从数据库中查询用户浏览的商品的具体信息
        # goods_li = GoodsSKU.objects.filter(id__in=sku_ids)
        #
        # goods_res = []
        # for id in sku_ids:
        #     for goods in goods_li:
        #         if id == goods.id:
        #             goods_res.append(goods)

        # 遍历获取用户浏览的商品信息
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        # 除了手动给模板文件传递的模板变量之外，django框架会把request.user也传给模板文件
        return render(request, 'user/user_center_info.html', locals())


# /user/order
class UserOrderView(LoginRequiredMixin, View):
    """用户中心订单页"""

    def get(self, request, page):
        """显示"""
        # 获取用户的订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')

        # 遍历获取商品的订单信息
        for order in orders:
            # 根据order_id查询订单商品信息
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)

            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                # 计算小计
                amount = order_sku.price * order_sku.count
                # 动态给order_sku增加属性amount，保存订单商品小计
                order_sku.amount = amount

            # 动态给order增加属性status_name，保存订单状态标题
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]

            # 动态给order增加属性order_skus，保存订单商品小计
            order.order_skus = order_skus

        # 分页
        paginator = Paginator(orders, 1)

        # 获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1
        if page > paginator.num_pages:
            page = 1

        # 获取第page页的Page实例对象
        order_page = paginator.page(page)

        # todo: 进行页码的控制，页面上最多显示5个页码
        # 1. 总页数小于5页，显示所有页码
        # 2. 如果当前页是前3页，显示1-5页页码
        # 3. 如果当前页是后3页， 显示后5页页码
        # 4. 其他情况，显示当前页的前2页，当前页，当前页的后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 使用模板
        return render(request, 'user/user_center_order.html', locals())


# /user/address
class UserSiteView(LoginRequiredMixin, View):
    """用户中心地址页"""

    def get(self, request):
        """显示"""
        page = 'address'
        # 获取登录用户对应的User对象
        user = request.user

        # 获取用户的默认收获地址
        # try:
        #     address = models.Address.objects.get(user=user, is_default=True)
        # except models.Address.DoesNotExist:
        #     # 不存在默认收获地址
        #     address = None
        address = models.Address.objects.get_default_address(user)

        # 使用模板
        return render(request, 'user/user_center_site.html', locals())

    def post(self,request):
        """地址的添加"""
        # 接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 校验数据
        # 先判断数据的完整性
        if not all([receiver, addr, phone]):
            return render(request, 'user/user_center_site.html', {'errmsg': '信息不完整'})

        # 校验手机号
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user/user_center_site.html', {'errmsg': '手机格式不正确'})

        # 业务处理：地址添加
        # 如果用户已存在默认收货地址，添加的地址不作为默认收货地址，否则作为默认收货地址
        # 获取登录用户对应User对象
        user = request.user
        # try:
        #     address = models.Address.objects.get(user=user, is_default=True)
        # except models.Address.DoesNotExist:
        #     # 不存在默认收获地址
        #     address = None
        address = models.Address.objects.get_default_address(user)

        if address:
            is_default = False
        else:
            is_default = True

        # 添加地址
        models.Address.objects.create(user=user,
                                      receiver=receiver,
                                      addr=addr,
                                      zip_code=zip_code,
                                      phone=phone,
                                      is_default=is_default)

        # 返回应答,刷新地址页面
        return redirect(reverse('address'))  # get请求方式

