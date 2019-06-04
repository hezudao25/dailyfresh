from django.shortcuts import render, redirect, HttpResponse
from django.urls import reverse
import re
from user.models import User, Address
from goods.models import GoodsSKU
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.conf import settings
from celery_tasks.tasks import send_register_active_email
from django.contrib.auth import authenticate, login, logout
from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection
from order.models import OrderInfo, OrderGoods
from django.core.paginator import Paginator

# Create your views here.

class RegisterView(View):
    '''类视图'''
    def get(self, request):
        '''显示注册页面'''
        return render(request, 'register.html')

    def post(self, request):
        '''注册处理'''
        # 接受数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 进行数据校验
        # if not all(username, password, email):
        # return render(request, 'register.html', {'errmsg': '数据不完整'})
        # return HttpResponse("数据不完整")

        if username == '' or password == '' or email == '':
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': 'email格式不对'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            # 用户名已存在
            return render(request, 'register.html', {'errmsg': '此用户已经存在'})

        # 进行业务处理
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()
        # 发送 激活邮件http://127.0.0.1:8000/user/active/1
        token = user.generate_active_token()
        # 发送邮件
        # subject = '天天生鲜欢迎信息'
        # message = ''
        # html_message = '''<h1>%s,欢迎注册会员</h1><br>请点击下面链接激活<br>
        # <a href='http://127.0.0.1:8000/user/active/%s' target='blank'>http://127.0.0.1:8000/user/active/%s</a>
        # ''' % (user.username, token, token)
        # sender = settings.DEFAULT_FROM_EMAIL
        # recrice = [email]
        # send_mail(subject, message, sender, recrice, html_message=html_message)
        send_register_active_email.delay(email, username, token)
        # 返回应答
        return redirect(reverse('goods:index'))

class ActiveView(View):
    '''用户激活类视图'''
    def get(self, request, token):
        serizlizer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serizlizer.loads(token)
            # 获取待激活用户的id
            user_id = info['confirm']

            # 根据id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活链接已过期
            return HttpResponse('激活链接已过期')


class LoginView(View):
    '''用户登录类视图'''
    def get(self, request):
        '''用户登录页面'''
        # 判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        '''用户登录验证'''
        # 接受数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        rem = request.POST.get('rem')
        # 校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})

        # 业务处理：登录校验
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户密码正确
            if user.is_active:  # 用户已激活
                # 记录用户登录记录
                login(request, user)
                # 获取跳转URL
                next_url = request.GET.get('next', reverse('goods:index'))
                response = redirect(next_url)
                # 判断是否记住用户名
                if rem == 'on':
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')

                return response
            else:
                return render(request, 'login.html', {'errmsg': '账户未激活'})
        else:
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})



class LogoutView(View):
    '''用户退出'''
    def get(self, request):
        logout(request)

        return redirect(reverse('goods:index'))


# /user
class UserInfoView(LoginRequiredMixin, View):
    '''用户中心-信息页'''
    def get(self, request):
        '''显示'''
        # 获取个人信息
        user = request.user
        address = Address.objects.get_default_address(user)

        # 获取用户的历史浏览记录
        con = get_redis_connection('default')
        history_key = 'history_%d' % user.id
        # 获取用户最新浏览的5条
        sku_ids = con.lrange(history_key, 0, 4)
        # 从数据库中查询用户浏览的商品的具体显示
        good_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            good_li.append(goods)

        context = {'page': 'user',
                   'address': address,
                   'good_li': good_li}


        return render(request, 'user_center_info.html', context)


# /user/order
class UserOrderView(LoginRequiredMixin, View):
    '''用户中心-订单页'''
    def get(self, request, page):
        '''显示'''
        # 获取用户的 订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user)

        # 遍历获取订单商品信息
        for order in orders:
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)

            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                amount = order_sku.count*order_sku.price
                order_sku.amount = amount

            order.order_skus = order_skus
            order.order_status_name = OrderInfo.ORDER_STATUS[str(order.order_status)]

        # 分页
        paginator = Paginator(orders, 1)
        # 获取页码
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page页的实例对象
        order_page = paginator.page(page)

        #  控制显示5页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 1, page + 3)

        # 组织上下文
        context = {
            'order_page': order_page,
            'pages': pages,
            'page': 'order'
        }

        return render(request, 'user_center_order.html', context)


# /user/address
class AddressView(LoginRequiredMixin, View):
    '''用户中心-地址页'''
    def get(self, request):
        '''显示'''
        # 获取用户的默认地址
        user = request.user
        address = Address.objects.get_default_address(user)

        return render(request, 'user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        '''地址添加'''

        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        if not all([receiver, addr, zip_code, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})

        # 验证手机号码
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '手机格式不对'})

        # 业务处理：地址添加
        # 如果用户已存在默认地址，则不作为
        user = request.user

        address = Address.objects.get_default_address(user)

        if address:
            is_default = False
        else:
            is_default = True

        address = Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)

        return redirect(reverse('user:address'))