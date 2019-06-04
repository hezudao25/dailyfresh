from celery import Celery
from django.core.mail import send_mail
from django.conf import settings
from django.template import loader
import os
# import django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')
# django.setup()
from goods.models import GoodsType, IndexGoodsBanner, IndexPromotioBanner, IndexTypeGoodsBanner

# 创建一个celery的实力对象
app = Celery('celery_tasks.tasks', broker='redis://192.168.72.136:6379/8')


# 定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
    '''发送激活邮件'''
    subject = '天天生鲜欢迎信息'
    message = ''
    html_message = '''<h1>%s,欢迎注册会员</h1><br>请点击下面链接激活<br>
            <a href='http://127.0.0.1:8000/user/active/%s' target='blank'>http://127.0.0.1:8000/user/active/%s</a> 
            ''' % (username, token, token)
    sender = settings.DEFAULT_FROM_EMAIL
    recrice = [to_email]
    send_mail(subject, message, sender, recrice, html_message=html_message)


@app.task
def generate_static_index_html():
    '''生产首页静态页面'''
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

    # 获取购物车商品数目
    cart_count = 0

    # 组织上下文
    context = {
        'types': types,
        'goods_banners': goods_banners,
        'promotion_banners': promotion_banners,
        'cart_count': cart_count
    }
    # 加载模板
    temp = loader.get_template('static_index.html')
    # 模板渲染
    static_index_html = temp.render(context)
    # 生产静态文件
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(save_path, 'w') as f:
        f.write(static_index_html)
