from django.shortcuts import render, redirect
from django.views.generic import View
from django.contrib.auth import authenticate
from django_redis import get_redis_connection
from django.core.cache import cache
from goods.models import GoodsType, IndexGoodsBanner, IndexPromotioBanner, IndexTypeGoodsBanner, GoodsSKU
from order.models import OrderGoods
from django.core.paginator import Paginator
# Create your views here.

class IndexView(View):

    def get(self, request):
        '''显示首页'''
        context = cache.get('index_page_data')
        if context is None:
            # 获取首页商品的分类信息
            types = GoodsType.objects.all()

            # 获取轮播商品信息
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')

            # 获取首页促销活动信息
            promotion_banners = IndexPromotioBanner.objects.all().order_by('index')

            # 获取首页分类商品展示信息
            for type in types:
                # 获取type种类商品的图片展示信息
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1)
                # 获取文字展示信息
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0)
                # 动态增加属性
                type.image_banners = image_banners
                type.title_banners = title_banners

            context = {
                'types': types,
                'goods_banners': goods_banners,
                'promotion_banners': promotion_banners,

            }

            # 设置缓存
            cache.set('index_page_data', context, 3600)


        # 获取购物车商品数目
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)


        # 组织上下文
        context.update(cart_count=cart_count)

        return render(request, 'index.html', context)


class DetailView(View):
    '''详情页'''
    def get(self, request, goods_id):
        '''显示详细页'''
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在
            return redirect(reversed("goods:index"))

        # 获取 商品分类
        types =GoodsType.objects.all()

        # 获取 商品评论
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='')

        # 获取最新商品
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]

        # 获取同一个SPU的其他规格的商品
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=goods_id)

        # 获取购物车商品数目
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

            # 添加用户的历史浏览记录
            conn = get_redis_connection('default')
            history_key = 'histry_%d' % user.id
            # 先移除
            conn.lrem(history_key, 0, goods_id)
            # 后插入
            conn.lpush(history_key, goods_id)
            # 只保存最新5条
            conn.ltrim(history_key, 0, 4)

        context = {
            'sku': sku,
            'sku_orders': sku_orders,
            'new_skus': new_skus,
            'cart_count': cart_count,
            'same_spu_skus': same_spu_skus
        }
        return render(request, 'detail.html', context)


# 种类 页码 排序
# /list/分类id/页码?sort=排序方式
class ListView(View):
    '''列表页'''
    def get(self, request, type_id, page_id):
        '''显示列表页'''
        # 获取分类信息
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            # 分类不存在
            return redirect(reversed('goods:index'))

        # 获取商品的分类信息
        types = GoodsType.objects.all()

        # 获取 排序 default 默认ID，price 价格 hot 销量
        sort = request.GET.get('sort')
        if sort =='hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
        elif sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        # 分页
        paginator = Paginator(skus, 1)
        # 获取页码
        try:
            page = int(page_id)
        except Exception as e:
            page = 1

        # if page >= Paginator.num_pages:
        #     page = Paginator.num_pages

        # 获取第page页的实例对象
        skus_page = paginator.page(page)

        #  控制显示5页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages+1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages =range(num_pages-4, num_pages+1)
        else:
            pages = range(page-1, page+3)


        # 获取最新商品
        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]

        # 获取购物车商品数目
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)


        # 组织上下文
        context = {
            'type': type,
            'types': types,
            'skus_page': skus_page,
            'new_skus': new_skus,
            'cart_count': cart_count,
            'sort': sort,
            'pages': pages
        }

        return render(request, 'list.html', context)


