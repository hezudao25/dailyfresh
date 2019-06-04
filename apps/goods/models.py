from datetime import datetime
from django.db import models
from db.base_model import BaseModel
from tinymce.models import HTMLField  # 使用富文本编辑框要在settings文件中安装
# 将一对多的关系维护在GoodsInfo中维护，另外商品信息与分类信息都属于重要信息需要使用逻辑删除


class GoodsType(BaseModel):
    # 商品分类信息  水果 海鲜等
    name = models.CharField(max_length=20, verbose_name="分类")
    logo = models.CharField(max_length=20, verbose_name='标识')
    image = models.ImageField(upload_to='type', verbose_name='分类图片')

    class Meta:
        db_table = 'goods_type'
        verbose_name = "商品类型"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

class GoodsSKU(BaseModel):
    '''商品SKU模型类'''
    status_choices = (
        (0, '下线'),
        (1, '上线'),
    )
    type = models.ForeignKey('GoodsType', on_delete=models.CASCADE, verbose_name="分类")
    goods = models.ForeignKey('Goods', on_delete=models.CASCADE, verbose_name="商品SPU")
    name = models.CharField(max_length=20, verbose_name="商品名称", unique=True)
    image = models.ImageField(verbose_name='商品图片', upload_to='goods', null=True, blank=True)  # 商品图片
    price = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="商品价格")  # 商品价格小数位为两位，整数位为3位
    unite = models.CharField(max_length=20, verbose_name="商品单位")
    click = models.IntegerField(verbose_name="点击量", default=0, null=False)
    desc = models.CharField(max_length=200, verbose_name="简介")
    stock = models.IntegerField(verbose_name="库存", default=1)
    sales = models.IntegerField(default=0, verbose_name='商品销量')
    status = models.SmallIntegerField(default=1, choices=status_choices, verbose_name='商品状态')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'goods_sku'
        verbose_name = '商品'
        verbose_name_plural = verbose_name


class Goods(BaseModel):
    '''商品SPU模型类'''
    name = models.CharField(max_length=20, verbose_name='商品SPU名称')
    detail = HTMLField(blank=True, verbose_name='商品详情')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'goods'
        verbose_name = '商品SPU'
        verbose_name_plural = verbose_name

class GoodsImage(BaseModel):
    '''商品图片类'''
    sku = models.ForeignKey(GoodsSKU, on_delete=models.CASCADE, verbose_name="商品")
    image = models.ImageField(upload_to='banner', verbose_name='图片')
    index = models.SmallIntegerField(default=0, verbose_name='展示顺序')

    def __str__(self):
        return self.sku

    class Meta:
        db_table = 'goods_image'
        verbose_name = '商品图片'
        verbose_name_plural = verbose_name


class IndexGoodsBanner(BaseModel):
    '''首页轮播商品展示模型类'''
    sku = models.ForeignKey(GoodsSKU, on_delete=models.CASCADE, verbose_name="商品")
    image = models.ImageField(upload_to='banner', verbose_name='图片')
    index = models.SmallIntegerField(default=0, verbose_name='展示顺序')

    class Meta:
        db_table = 'goods_banner'
        verbose_name = '首页轮播图片'
        verbose_name_plural = verbose_name


class IndexTypeGoodsBanner(BaseModel):
    '''首页分类商品展示模型类'''
    DISPLAY_TYPE_CHOICES = (
        (0, '标题'),
        (1, '图片')
    )
    type = models.ForeignKey(GoodsType, verbose_name='商品类型', on_delete=models.CASCADE,)
    sku = models.ForeignKey(GoodsSKU, verbose_name='商品SKU', on_delete=models.CASCADE,)
    display_type = models.SmallIntegerField(default=1, choices=DISPLAY_TYPE_CHOICES, verbose_name='展示类型')
    index = models.SmallIntegerField(default=0, verbose_name='展示顺序')

    def sku_name(self):
        """返回父级区域名"""
        if self.sku is None:
            return ''

        return self.sku.name

    # 指定方法列显示的名称
    sku_name.short_description = '商品'
    # 方法列默认不能排序，需要指定方法列按id进行排序


    sku_name.admin_order_field = 'id'

    class Meta:
        db_table = 'index_type_goods'
        verbose_name = '首页分类展示商品'
        verbose_name_plural = verbose_name


class IndexPromotioBanner(BaseModel):
    '''首页促销活动模型类'''
    name = models.CharField(max_length=20, verbose_name='活动名称')
    url = models.URLField(verbose_name='活动链接')
    image = models.ImageField(upload_to='banner', verbose_name='图片')
    index = models.SmallIntegerField(default=0, verbose_name='展示顺序')

    class Meta:
        db_table = 'index_promotion'
        verbose_name = '首页促销活动'
        verbose_name_plural = verbose_name
