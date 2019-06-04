from django.urls import path, include, re_path
from .views import OrderPlaceView, OrderCommitView
app_name = 'order'
urlpatterns = [
    path('place', OrderPlaceView.as_view(), name='place'),
    path('commit', OrderCommitView.as_view(), name='commit'),
]
