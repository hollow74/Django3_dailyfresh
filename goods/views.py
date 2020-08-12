from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse

from django.views import View
from django_redis import get_redis_connection

from order.models import OrderGoods
from . import models

# http://127.0.0.1:8000
# /index
class IndexView(View):
    """首页"""
    def get(self,request):
        """显示首页"""
        # 尝试从缓存中获取数据 -- cache.get(key)
        context = cache.get('index_page_data')
        if context is None:
            print('设置缓存')
            # 缓存中没有数据
            # 获取商品的种类信息
            types = models.GoodsType.objects.all()

            # 获取首页轮播商品信息
            goods_banners = models.IndexGoodsBanner.objects.all().order_by('index')

            # 获取首页促销活动信息
            promotion_banners = models.IndexPromotionBanner.objects.all().order_by('index')

            # 获取首页分类商品展示信息
            for type in types:    # GoodsType
                # 获取type种类在首页分类商品的图片展示信息
                image_banners = models.IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
                # 获取type种类在首页分类商品的文字展示信息
                title_banners = models.IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

                # 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
                type.image_banners = image_banners
                type.title_banners = title_banners

            # 组织模板上下文
            context = {'types': types,
                       'goods_banners': goods_banners,
                       'promotion_banners': promotion_banners,
                       }

            # 设置缓存
            # key value timeout
            # cache.set('index_page_data', locals(), 3600)   # 报错，不可序列化
            cache.set('index_page_data', context, 3600)

        # 获取用户购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        context.update(cart_count=cart_count)

        # 使用模板
        return render(request, 'goods/index.html', context)


# /goods/商品ID
class DetailView(View):
    """详情页"""
    def get(self, request, goods_id):
        """显示详情页"""
        # 获取具体商品信息
        try:
            sku = models.GoodsSKU.objects.get(id=goods_id)
        except models.GoodsSKU.DoesNotExist:
            # 商品不存在
            return redirect(reverse('index'))

        # 获取商品分类信息
        types = models.GoodsType.objects.all()

        # 获取商品评论信息
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='')

        # 获取新品信息
        new_skus = models.GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]

        # 获取同一个SPU的其他规格商品(SPU的应用)
        same_spu_skus = models.GoodsSKU.objects.filter(goods=sku.goods).exclude(id=goods_id)

        # 获取用户购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

            # 添加用户的历史浏览记录
            conn = get_redis_connection('default')
            history_key = 'history_%d' % user.id
            # 移除列表中goods_id
            conn.lrem(history_key, 0, goods_id)
            # 在列表左侧插入goods_id
            conn.lpush(history_key, goods_id)
            # 只保存用户浏览的五条信息
            conn.ltrim(history_key, 0, 4)

        return render(request, 'goods/detail.html', locals())


# 种类id 页码 排序方式
# restful api --> 请求一种资源
# /list?type=种类id&page=页码&sort=排序方式
# /list/种类id/页码/排序方式
# /list/种类id/页码?sort=排序方式 √
class ListView(View):
    """列表页面"""
    def get(self, request, type_id, page):
        """显示列表页"""
        # 先获取种类的信息
        try:
            type = models.GoodsType.objects.get(id=type_id)
        except models.GoodsType.DoesNotExist:
            # 种类不存在，跳转到首页
            return redirect(reverse('index'))

        # 获取商品的分类信息
        types = models.GoodsType.objects.all()

        # 获取分类商品的信息 -- 按照不同排序方式
        # sort=default  按照默认id排序
        # sort=price 按照商品价格排序
        # sort=hot  按照商品销量排序
        sort = request.GET.get('sort')
        if sort == 'price':
            skus = models.GoodsSKU.objects.filter(type=type).order_by('price')
        elif sort == 'hot':
            skus = models.GoodsSKU.objects.filter(type=type).order_by('-sales')
        else:
            sort = 'default'
            skus = models.GoodsSKU.objects.filter(type=type).order_by('-id')

        # 对数据进行分页
        paginator = Paginator(skus, 1)

        # 获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1
        if page > paginator.num_pages:
            page = 1

        # 获取第page页的Page实例对象
        skus_page = paginator.page(page)

        # todo: 进行页码的控制，页面上最多显示5个页码
        # 1. 总页数小于5页，显示所有页码
        # 2. 如果当前页是前3页，显示1-5页页码
        # 3. 如果当前页是后3页， 显示后5页页码
        # 4. 其他情况，显示当前页的前2页，当前页，当前页的后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages+1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages-4, num_pages+1)
        else:
            pages = range(page-2, page+3)

        # 获取新品信息
        new_skus = models.GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]

        # 获取用户购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        # # 组织模板上下文
        # context = {'type': type, 'types': types,
        #            'skus_page': skus_page,
        #            'new_skus': new_skus,
        #            'cart_count': cart_count,
        #            'sort': sort}

        return render(request, 'goods/list.html', locals())



