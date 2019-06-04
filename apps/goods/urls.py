from django.urls import path, include, re_path
#from apps.goods import views
from goods.views import IndexView, DetailView, ListView
app_name = 'goods'
urlpatterns = [
    re_path(r'^$', IndexView.as_view(), name='index'),
    path('<int:goods_id>', DetailView.as_view(), name='detail'),
    path('list/<int:type_id>/<int:page_id>', ListView.as_view(), name='list')

]
