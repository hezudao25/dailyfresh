from django.db import models
from db.base_model import BaseModel
from user.models import User


class OrderInfo(BaseModel):
    '''订单模型类'''
    PAY_METHODS = {
        '1': '货到付款',
        '2': '微信支付',
        '3': '支付宝',
        '4': '银联支付',
    }

    PAY_METHOD_CHOICES = (
        (1, '货到付款'),
        (2, '微信支付'),
        (3, '支付宝'),
        (4, '银联支付'),
    )
    ORDER_STATUS = {
        '1': '待支付',
        '2': '待发货',
        '3': '待收货',
        '4': '待评论',
        '5': '已完成',
    }
    ORDEER_STATUS_CHOICES = (
        (1, '待支付'),
        (2, '待发货'),
        (3, '待收货'),
        (4, '待评论'),
        (5, '已完成'),
    )
    order_id = models.CharField(max_length=20, primary_key=True, verbose_name="大订单号")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="订单用户")
    addr = models.ForeignKey('user.Address',default='', on_delete=models.CASCADE, verbose_name="订单用户")
    pay_method = models.SmallIntegerField(default=3, choices=PAY_METHOD_CHOICES, verbose_name='支付方式')
    total_count = models.IntegerField(default=1, verbose_name='商品数量')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品总价')
    transit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='运费')
    order_status = models.SmallIntegerField(default=1, choices=ORDEER_STATUS_CHOICES, verbose_name='订单状态')
    trade_no = models.CharField(max_length=128, verbose_name='支付编号')

    class Meta:
        db_table = 'order_info'
        verbose_name = "订单"
        verbose_name_plural = verbose_name


# 无法实现：真实支付，物流信息
class OrderGoods(BaseModel):
    '''订单商品模型类'''
    sku = models.ForeignKey('goods.GoodsSKU', on_delete=models.CASCADE, verbose_name="商品SKU")  # 关联商品信息
    order = models.ForeignKey(OrderInfo, on_delete=models.CASCADE, verbose_name="订单")
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="商品价格")
    count = models.IntegerField(default=1, verbose_name="商品数")
    comment = models.CharField(max_length=256, verbose_name='评论')

    class Meta:
        db_table = 'order_goods'
        verbose_name = "订单详情"
        verbose_name_plural = verbose_name

