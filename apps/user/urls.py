from django.urls import path, re_path
from user.views import RegisterView, LoginView, ActiveView, UserInfoView, UserOrderView, AddressView, LogoutView

app_name = 'user'
urlpatterns = [
    re_path(r'register$', RegisterView.as_view(), name='register'),
    path('active/<str:token>', ActiveView.as_view(), name='register_handle'),
    re_path(r'login$', LoginView.as_view(), name='login'),
    re_path(r'logout$', LogoutView.as_view(), name='logout'),
    re_path(r'order/(?P<page>[0-9]+)$', UserOrderView.as_view(), name='order'),
    path('address', AddressView.as_view(), name='address'),
    path('', UserInfoView.as_view(), name='info'),
]
