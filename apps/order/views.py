from django.shortcuts import render, redirect
from django.views.generic import View
from django.urls import reverse
from django_redis import get_redis_connection
from goods.models import GoodsSKU
from user.models import Address
from django.http import JsonResponse
from .models import OrderInfo, OrderGoods
from datetime import datetime
from django.db import transaction

# Create your views here.
class OrderPlaceView(View):
    '''提交订单页面显示'''
    def post(self, request):
        ''''''
        user = request.user
        # 获取 参数sku_ids
        sku_ids =request.POST.getlist('sku_ids')

        if not sku_ids:
            return redirect(reverse('cart:show'))

        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        skus = []
        total_count = 0
        total_price = 0
        # 遍历shu_ids获取用户要购买的商品信息
        for sku_id in sku_ids:
            # 根据商品的id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 获取用户购买的商品数量
            count = conn.hget(cart_key, sku_id)
            # 计算商品的小计
            amount = sku.price*int(count)
            # 动态增加属性
            sku.count = int(count)
            sku.amount = amount

            skus.append(sku)
            # 统计商品的总数量 和价格
            total_count += int(count)
            total_price += amount

        # 运费：实际开发是个子系统
        transit_price = 10

        # 实付款
        total_pay = total_price + transit_price
        # 地址
        addr = Address.objects.filter(user=user)

        # 组织上下文
        context = {
            'skus':skus,
            'total_count': total_count,
            'total_price': total_price,
            'transit_price': transit_price,
            'total_pay': total_pay,
            'addr': addr,
            'sku_ids': ','.join(sku_ids)
        }
        return render(request, 'place_order.html', context)


class OrderCommitView1(View):
    '''订单提交'''
    @transaction.atomic
    def post(self, request):
        ''''''
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '没有登录'})
        # 获取 参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')

        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法的支付方式'})

        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '非法的地址方式'})

        # todo: 创建订单核心业务
        # 组织参数
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        # 运费
        transit_price = 10

        # 总数目和价格
        total_count = 0
        total_price = 0

        # 创建事务保持点
        save_id = transaction.savepoint()
        try:
            # todo: 插入数据
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=addr,
                                             pay_method=pay_method,
                                             total_count=total_count,
                                             total_price=total_price,
                                             transit_price=transit_price)

            # todo: 向order_goods插入信息
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id

            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                # 获取商品的信息
                try:
                    # 加锁（悲观锁）select_for_update()
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                except GoodsSKU.DoesNotExist:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                count = conn.hget(cart_key, sku_id)
                # todo: 判断商品的库存
                if int(count) > sku.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})
                # todo : 添加信息
                OrderGoods.objects.create(order=order,
                                          sku=sku,
                                          count=count,
                                          price=sku.price)

                # todo: 更新商品的库存和销量
                sku.stock -= int(count)
                sku.sales += int(count)
                sku.save()

                # todo: 累计商品的总数量和总价格
                amount = sku.price*int(count)
                total_count += int(count)
                total_price += amount

            # todo: 更新订单信息表中的总数量和价格
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as e:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 7, 'errmsg': '提交失败'})

        # 提交事务
        transaction.savepoint_commit(save_id)

        # todo: 清楚购物车中对应的记录
        conn.hdel(cart_key, *sku_ids)

        return JsonResponse({'res': 5, 'errmsg': '创建成功'})


class OrderCommitView(View):
    '''订单提交'''
    @transaction.atomic
    def post(self, request):
        ''''''
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '没有登录'})
        # 获取 参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')

        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法的支付方式'})

        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '非法的地址方式'})

        # todo: 创建订单核心业务
        # 组织参数
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        # 运费
        transit_price = 10

        # 总数目和价格
        total_count = 0
        total_price = 0

        # 创建事务保持点
        save_id = transaction.savepoint()
        try:
            # todo: 插入数据
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=addr,
                                             pay_method=pay_method,
                                             total_count=total_count,
                                             total_price=total_price,
                                             transit_price=transit_price)

            # todo: 向order_goods插入信息
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id

            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                for i in range(3):  # 尝试3次
                    # 获取商品的信息
                    try:
                        print(sku_id)
                        sku = GoodsSKU.objects.get(id=sku_id)
                    except GoodsSKU.DoesNotExist:
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                    count = conn.hget(cart_key, sku_id)
                    # todo: 判断商品的库存
                    if int(count) > sku.stock:
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

                    # todo: 更新商品的库存和销量
                    orgin_stock = sku.stock
                    new_stock = orgin_stock - int(count)
                    new_sales = orgin_stock + int(count)

                    # 使用乐观锁
                    res = GoodsSKU.objects.filter(id=sku.id, stock=orgin_stock).update(stock=new_stock, sales=new_sales)
                    if res == 0:
                        if i == 2:
                            transaction.savepoint_rollback(save_id)
                            return JsonResponse({'res': 8, 'errmsg': '商品库存不足'})
                        continue

                    # todo : 添加信息
                    OrderGoods.objects.create(order=order,
                                              sku=sku,
                                              count=count,
                                              price=sku.price)

                    # todo: 累计商品的总数量和总价格
                    amount = sku.price*int(count)
                    total_count += int(count)
                    total_price += amount

                    # 跳出循环
                    break

            # todo: 更新订单信息表中的总数量和价格
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as e:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 7, 'errmsg': '提交失败'})

        # 提交事务
        transaction.savepoint_commit(save_id)

        # todo: 清楚购物车中对应的记录
        conn.hdel(cart_key, *sku_ids)

        return JsonResponse({'res': 5, 'errmsg': '创建成功'})

