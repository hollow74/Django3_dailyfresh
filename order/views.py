import os
from datetime import datetime

from alipay import AliPay, ISVAliPay
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection

from dailyfresh import settings
from goods.models import GoodsSKU
from user.models import Address
from utils.mixin import LoginRequiredMixin
from . import models
# Create your views here.


# /order/place
# 不涉及js,可以使用LoginRequiredMixin登录校验
class OrderPlaceView(LoginRequiredMixin, View):
    """提交订单页面显示"""
    def post(self, request):
        """提交订单页面显示"""
        # 获取登录的用户
        user = request.user

        # 获取参数sku_ids
        sku_ids = request.POST.getlist('sku_ids')  # [1,8]

        # 校验数据
        if not sku_ids:
            # 跳转到购物车页面
            return redirect(reverse('show'))

        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        skus = []
        # 保存商品的总件数和总价格
        total_count = 0
        total_price = 0
        # 遍历sku_ids，获取用户要购买的商品的信息
        for sku_id in sku_ids:
            # 根据商品的id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 获取用户所要购买的商品的数量
            count = conn.hget(cart_key, sku_id)
            count = int(count)
            # 计算商品的小计
            amount = sku.price * int(count)
            # 动态给sku增加属性count，保存购买商品的数量
            sku.count = count
            # 动态给sku增加属性amount，保存购买商品的小计
            sku.amount = amount
            skus.append(sku)
            # 累加计算商品的总件数和总价格
            total_count += int(count)
            total_price += amount

        # 运费:实际开发的时候，属于一个子系统
        transit_price = 10    # 本项目写死

        # 实付款
        total_pay = total_price + transit_price

        # 获取用户的收件地址
        addrs = Address.objects.filter(user=user)

        sku_ids = ','.join(sku_ids)    # [1,8] -> '1,2,3,4,5,6,7,8'

        # 返回响应
        return render(request, 'order/place_order.html', locals())


# 前端传递的数据:地址id(addr_id) 支付方式(pay_method) 用户要购买的商品(sku_ids)
# mysql事务: 一组sql操作，要么都成功，要么都失败
# 高并发: 秒杀
# 支付宝支付

# /order/submit
# 悲观锁
class OrderCommitView1(View):
    """订单创建"""
    @transaction.atomic
    def post(self, request):
        """订单创建"""
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收数据
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')  # 1,2,3

        # 校验数据
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '参数不完整'})

        # 校验支付方式
        if pay_method not in models.OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法的支付方式'})

        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            # 地址不存在
            return JsonResponse({'res': 3, 'errmsg': '地址非法'})

        # 业务处理
        # todo: 创建订单核心业务
        # 组织参数
        # 订单id:20200809212324+用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S')+str(user.id)

        # 运费
        transit_price = 10

        # 总数目和总金额
        total_count = 0
        total_price = 0

        # 设置事务保存点
        save_id = transaction.savepoint()
        try:
            # todo: 向df_order_info表中添加一条记录（核心）
            order = models.OrderInfo.objects.create(order_id=order_id,
                                                    user=user,
                                                    addr=addr,
                                                    pay_method=pay_method,
                                                    total_count=total_count,
                                                    total_price=total_price,
                                                    transit_price=transit_price)

            # todo: 用户的订单中有几个商品，需要向df_order_goods表中添加几条记录（核心）
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id

            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                # 获取商品信息
                try:
                    # select * from df_goods_sku where id=sku_id for update;
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                except:
                    # 商品不存在
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                # print('user:%d stock:%d' % (user.id, sku.stock))
                # import time
                # time.sleep(10)

                # 从redis中获取用户所要购买的商品的数量
                count = conn.hget(cart_key, sku_id)

                # todo: 判断商品的库存
                if int(count) > sku.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

                # todo: 向df_order_goods表中添加一条记录
                models.OrderGoods.objects.create(order=order,
                                                 sku=sku,
                                                 count=count,
                                                 price=sku.price)

                # todo: 更新商品的库存和销量
                sku.stock -= int(count)
                sku.sales += int(count)
                sku.save()

                # todo:累加计算订单商品的总数量和总价格
                amount = sku.price * int(count)
                total_count += int(count)
                total_price += amount

            # todo: 更新订单信息表中的商品总数量和总价格
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as e:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 7, 'errmsg': '下单失败'})

        # 提交事务
        transaction.savepoint_commit(save_id)

        # todo: 清除用户购物车中对应的记录
        # *sku_ids 是对列表拆包 [1,2,3] -> 1,2,3
        conn.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '创建成功'})


# /order/submit
# 乐观锁
class OrderCommitView(View):
    """订单创建"""
    @transaction.atomic
    def post(self, request):
        """订单创建"""
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收数据
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')  # 1,2,3

        # 校验数据
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '参数不完整'})

        # 校验支付方式
        if pay_method not in models.OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法的支付方式'})

        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            # 地址不存在
            return JsonResponse({'res': 3, 'errmsg': '地址非法'})

        # 业务处理
        # todo: 创建订单核心业务
        # 组织参数
        # 订单id:20200809212324+用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S')+str(user.id)

        # 运费
        transit_price = 10

        # 总数目和总金额
        total_count = 0
        total_price = 0

        # 设置事务保存点
        save_id = transaction.savepoint()
        try:
            # todo: 向df_order_info表中添加一条记录（核心）
            order = models.OrderInfo.objects.create(order_id=order_id,
                                                    user=user,
                                                    addr=addr,
                                                    pay_method=pay_method,
                                                    total_count=total_count,
                                                    total_price=total_price,
                                                    transit_price=transit_price)

            # todo: 用户的订单中有几个商品，需要向df_order_goods表中添加几条记录（核心）
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id

            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                for i in range(3):
                    # 获取商品信息
                    try:
                        sku = GoodsSKU.objects.get(id=sku_id)
                    except:
                        # 商品不存在
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                    # 从redis中获取用户所要购买的商品的数量
                    count = conn.hget(cart_key, sku_id)
                    count = int(count)

                    # todo: 判断商品的库存
                    if count > sku.stock:
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

                    # todo: 更新商品的库存和销量
                    origin_stock = sku.stock
                    new_stock = origin_stock - count
                    new_sales = sku.sales + count

                    # print('user:%d times:%d stock:%d' % (user.id, i, sku.stock))
                    # import time
                    # time.sleep(10)

                    # update df_goods_sku set stock=new_stock, sales=new_sales
                    # where id=sku_id and stock=origin_stock;
                    # 返回受影响的行数(1行),放在向df_order_goods表中添加记录之前，防止重复加数据
                    res = GoodsSKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock, sales=new_sales)
                    if res == 0:
                        if i == 2:
                            # 尝试的第3次
                            transaction.savepoint_rollback(save_id)
                            return JsonResponse({'res': 7, 'errmsg': '下单失败！'})
                        continue

                    # todo: 向df_order_goods表中添加一条记录
                    models.OrderGoods.objects.create(order=order,
                                                     sku=sku,
                                                     count=count,
                                                     price=sku.price)

                    # todo:累加计算订单商品的总数量和总价格
                    amount = sku.price * count
                    total_count += count
                    total_price += amount

                    # 跳出循环
                    break

            # todo: 更新订单信息表中的商品总数量和总价格
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as e:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 7, 'errmsg': '下单失败!'})

        # 提交事务
        transaction.savepoint_commit(save_id)

        # todo: 清除用户购物车中对应的记录
        # *sku_ids 是对列表拆包 [1,2,3] -> 1,2,3
        conn.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '创建成功'})


# ajax post
# 前端传递的参数:订单id(order_id)
# /order/pay
class OrderPayView(View):
    """订单支付"""
    def post(self, request):
        """订单支付"""
        # 用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        order_id = request.POST.get('order_id')

        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单id'})

        try:
            order = models.OrderInfo.objects.get(order_id=order_id,
                                                 user=user,
                                                 pay_method=3,
                                                 order_status=1)
        except models.OrderInfo.DoesNotExist:
            # 订单不存在
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # 业务处理:使用python sku调用支付宝的支付接口
        # 初始化
        alipay = AliPay(
            appid='2021000116677700',    # 应用id
            app_notify_url=None,    # 默认回调url
            app_private_key_string=open('order/app_private_key.pem').read(),
            alipay_public_key_string=open('order/alipay_public_key.pem').read(),    # 支付宝的公钥，验证支付宝回传消息使用，不是自己的公钥
            sign_type='RSA2',    # RSA 或者 RSA2
            debug=True,    # 默认False访问真实地址,True为访问沙箱地址
        )

        # 调用支付接口
        # 电脑网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
        total_pay = order.total_price + order.transit_price  # Decimal,不能序列化，需要转化为字符串
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 订单id
            total_amount=str(total_pay),  # 支付总金额
            subject='天天生鲜%s' % order_id,
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )

        # 返回应答
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res': 3, 'pay_url': pay_url})


# /order/check
class CheckPayView(View):
    """查看订单支付的结果"""
    def post(self, request):
        """查看订单支付的结果"""
        # 用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        order_id = request.POST.get('order_id')

        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单id'})

        try:
            order = models.OrderInfo.objects.get(order_id=order_id,
                                                 user=user,
                                                 pay_method=3,
                                                 order_status=1)
        except models.OrderInfo.DoesNotExist:
            # 订单不存在
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # 业务处理:使用python sku调用支付宝的支付结果查询接口
        # 初始化
        alipay = AliPay(
            appid='2021000116677700',  # 应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_string=open('order/app_private_key.pem').read(),
            alipay_public_key_string=open('order/alipay_public_key.pem').read(),  # 支付宝的公钥，验证支付宝回传消息使用，不是自己的公钥
            sign_type='RSA2',  # RSA 或者 RSA2
            debug=True,  # 默认False访问真实地址,True为访问沙箱地址
        )

        # 调用支付宝的交易查询接口
        while True:
            response = alipay.api_alipay_trade_query(order_id)

            # response = {
            #         "trade_no": "2017032121001004070200176844",  # 支付宝交易号
            #         "code": "10000",  # 接口调用是否成功
            #         "invoice_amount": "20.00",
            #         "open_id": "20880072506750308812798160715407",
            #         "fund_bill_list": [
            #             {
            #                 "amount": "20.00",
            #                 "fund_channel": "ALIPAYACCOUNT"
            #             }
            #         ],
            #         "buyer_logon_id": "csq***@sandbox.com",
            #         "send_pay_date": "2017-03-21 13:29:17",
            #         "receipt_amount": "20.00",
            #         "out_trade_no": "out_trade_no15",
            #         "buyer_pay_amount": "20.00",
            #         "buyer_user_id": "2088102169481075",
            #         "msg": "Success",
            #         "point_amount": "0.00",
            #         "trade_status": "TRADE_SUCCESS",  # 支付结果
            #         "total_amount": "20.00"
            #     }

            code = response.get('code')
            trade_status = response.get('trade_status')
            if code == '10000' and trade_status == "TRADE_SUCCESS":
                # 支付成功
                # 获取支付宝交易号
                trade_no = response.get('trade_no')
                # 更新订单状态
                order.trade_no = trade_no
                order.order_status = 4    # 待评价
                order.save()
                # 返回结果
                return JsonResponse({'res': 3, 'message': '支付成功'})

            elif code == '40004' or (code == '10000' and trade_status == "WAIT_BUYER_PAY"):
                # 等待买家付款
                # 业务处理失败，可能一会儿就会成功(40004)
                import time
                time.sleep(5)
                continue

            else:
                # 支付出错
                print(code)
                return JsonResponse({'res': 4, 'errmsg': '支付失败'})


# /order/comment
# 不涉及 ajax 可以使用LoginRequiredMixin登录验证
class CommentView(LoginRequiredMixin, View):
    """订单评论"""
    def get(self, request, order_id):
        """提供评论页面"""
        user = request.user

        # 校验数据
        if not order_id:
            return redirect(reverse('order'))

        try:
            order = models.OrderInfo.objects.get(order_id=order_id, user=user)
        except models.OrderInfo.DoesNotExist:
            return redirect(reverse('order'))

        # 根据订单的状态获取订单的状态标题
        order.status_name = models.OrderInfo.ORDER_STATUS[order.order_status]

        # 获取订单商品信息
        order_skus = models.OrderGoods.objects.filter(order_id=order_id)
        for order_sku in order_skus:
            # 计算商品的小计
            amount = order_sku.count * order_sku.price
            # 动态给order_sku增加属性amount,保存商品小计
            order_sku.amount = amount
        # 动态给order增加属性order_skus, 保存订单商品信息
        order.order_skus = order_skus

        # 使用模板
        return render(request, "order/order_comment.html", {'order': order})

    def post(self, request, order_id):
        """处理评论内容"""
        user = request.user
        # 校验数据
        if not order_id:
            return redirect(reverse('order'))

        try:
            order = models.OrderInfo.objects.get(order_id=order_id, user=user)
        except models.OrderInfo.DoesNotExist:
            return redirect(reverse('order'))

        # 获取评论条数
        total_count = request.POST.get("total_count")
        total_count = int(total_count)

        # 循环获取订单中商品的评论内容
        for i in range(1, total_count + 1):
            # 获取评论的商品的id
            sku_id = request.POST.get("sku_%d" % i)   # sku_1 sku_2
            # 获取评论的商品的内容
            content = request.POST.get('content_%d' % i, '')   # content_1 content_2 content_3
            try:
                order_goods = models.OrderGoods.objects.get(order=order, sku_id=sku_id)
            except models.OrderGoods.DoesNotExist:
                continue

            order_goods.comment = content
            order_goods.save()

        order.order_status = 5   # 已完成
        order.save()

        return redirect(reverse('order', kwargs={"page": 1}))

