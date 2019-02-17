import json
import time

from django.http import HttpResponse
from django.core import serializers
from Cart import redis

# Create your views here.
from Data.models import Menu, MenuType, Order, Desk, User, OrderDetail


def get_menu_type(request):
    data = MenuType.objects.prefetch_related('Menus').order_by("Sort").all()
    result = []
    for i in data:
        menus = []
        for j in i.Menus.all():
            menu = {
                'Name': j.Name,
                'Price': float(j.Price),
                'Img': str(j.Img)
            }
            menus.append(menu)
        data = {
            'Name': i.Name,
            'Menus': menus
        }
        result.append(data)
    return HttpResponse(json.dumps(result))


def get_cache(request, desk):
    cache_list = redis.get_cache(desk)
    for i in cache_list:
        i['img'] = str(Menu.objects.get(Name=i['name']).Img)
    order_id = int(round(time.time() * 1000))
    result = {"id": order_id, "detail": cache_list}
    return HttpResponse(json.dumps(result))


def get_order(request, order_id):
    return HttpResponse(serializers.serialize('json', Order.objects.filter(pk=order_id)))


def set_order(request):
    # 获取参数
    order_id = request.POST['id']
    user = User.objects.get(OpenId=request.POST.get('open_id'))
    desk = Desk.objects.get(DeskMum=request.POST.get('desk'))
    comments = request.POST['comments']
    Order.objects.create(OrderId=order_id, User=user, Desk=desk, Comments=comments)
    # save cache in redis
    order = Order.objects.get(order_id=order_id)
    total = 0
    for i in redis.get_cache(desk):
        menu = Menu.objects.get(i['name'])
        OrderDetail.objects.create(menu=menu, order=order, Number=i['num'])
        total += menu.Price * i['num']
    order.Total = total
    order.save()
