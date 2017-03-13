from django.template import Context, loader
from django.http import HttpResponse, HttpResponsePermanentRedirect
#from django.http import Http404
import re
import datetime
import fpformat

from django.shortcuts import render, render_to_response, get_object_or_404
from django.db.models import Q
from django.db.models import Count
from django.db.models import Sum

from models import Room, Product, Member, Sale, StregForbudError, News

def __get_news():
    try:
        return News.objects.filter(stop_date__gte=datetime.datetime.now(), pub_date__lte=datetime.datetime.now()).get()
    except News.DoesNotExist:
        return None

def __get_productlist():
    l = Product.objects.filter(Q(active=True), Q(deactivate_date__gte=datetime.datetime.now()) | Q(deactivate_date__isnull=True)).order_by('id')
    #Magic to make the list sorted in two columns (A, B, C, D) =>
    # A C
    # B D
    return l
    low = l[:int(len(l)/2.0+0.5)] + [None]
    high = l[int(len(l)/2.0+0.5):] + [None]
    return [a for a in reduce(lambda x,y: x+y, zip(low, high)) if a]

def roomindex(request):
    return HttpResponsePermanentRedirect('/1/')
#    room_list = Room.objects.all().order_by('name', 'description')
#    return render(request, 'stregsystem/roomindex.html', {'room_list': room_list})

def index(request, room_id):
    room = get_object_or_404(Room, pk=int(room_id))
    product_list = __get_productlist()
    news = __get_news()
    return render(request, 'stregsystem/index.html', locals())

def sale(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    news = __get_news()
    product_list = __get_productlist()
    
    quickbuy_list = re.split('\s+', request.POST['quickbuy'].strip())

    username = quickbuy_list[0]
    if username.strip() == "":
        return render(request, 'stregsystem/index.html', locals())
    try:
        member = Member.objects.get(username=username, active=True)
        bought_ids = map(int, quickbuy_list[1:])
    except Member.DoesNotExist:
        return render(request, 'stregsystem/error_usernotfound.html', locals())
    #XXX disabled multibuy
    if len(bought_ids) == 1:
        return quicksale(request, room, member, bought_ids)
    else:
        return usermenu(request, room, member, None)

def quicksale(request, room, member, bought_ids):
    bought_ids_count = {}
    news = __get_news()
    product_list = __get_productlist()
    for i in bought_ids:
        bought_ids_count[i] = bought_ids_count.get(i,0) + 1

    try:
        info = {}
        for i in bought_ids_count.keys():
            product = Product.objects.get(Q(pk=i), Q(active=True), Q(deactivate_date__gte=datetime.datetime.now()) | Q(deactivate_date__isnull=True))
            info[i] = {'count': bought_ids_count[i], 'product': product}
        cost = reduce(lambda s, i: s + i['count']*i['product'].price, info.values(), 0)
    except Product.DoesNotExist:
        return usermenu(request, room, member, None)
    bought_list = info.values()

    try:
        for i in bought_ids:
            product = info[i]['product']
            s = Sale(member=member,
                     product=product,
                     room=room,
                     price=product.price)
            s.save()
    except StregForbudError:
        return render(request, 'stregsystem/error_stregforbud.html', locals())
    
    promille = member.calculate_alcohol_promille()
    
    return render(request, 'stregsystem/index_sale.html', locals())

def usermenu(request, room, member, bought):
    negative_balance = member.balance < 0
    product_list = __get_productlist()
    news = __get_news()
    promille = member.calculate_alcohol_promille()
    if member.has_stregforbud():
        return render(request, 'stregsystem/error_stregforbud.html', locals())
    else:
        return render(request, 'stregsystem/menu.html', locals())

def __get_total_by_product(member):
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("""SELECT name, SUM(sale.price) 
                    FROM `stregsystem_sale` as `sale`, `stregsystem_product` as `product`
                    WHERE `member_id` = %s AND product.id = sale.product_id GROUP BY `product_id`""", [member.id])
    l = cursor.fetchall()
    l2 = []
    for a in l:
        l2.append((a[0], int(a[1])))

    return l2

def menu_userinfo(request, room_id, member_id):
    room = Room.objects.get(pk=room_id)
    news = __get_news()
    member = Member.objects.get(pk=member_id, active=True)
    
    last_sale_list = member.sale_set.order_by('-timestamp')[:10]
    try:
        last_payment = member.payment_set.order_by('-timestamp')[0]
    except IndexError:
        last_payment = None

    total_by_product = __get_total_by_product(member)
    total_sales = reduce(lambda s, i: s + i[1], total_by_product, 0)
    
    negative_balance = member.balance < 0
    stregforbud = member.has_stregforbud()

    return render(request, 'stregsystem/menu_userinfo.html', locals())

def menu_sale(request, room_id, member_id, product_id=None):
    room = Room.objects.get(pk=room_id)
    news = __get_news()
    member = Member.objects.get(pk=member_id, active=True)
    product = None
    try:
        product = Product.objects.get(Q(pk=product_id), Q(active=True), Q(deactivate_date__gte=datetime.datetime.now()) | Q(deactivate_date__isnull=True))
        s = Sale(member=member,
                 product=product,
                 room=room,
                 price=product.price)
        s.save()
    except Product.DoesNotExist:
        pass
    except StregForbudError:
        return render(request, 'stregsystem/error_stregforbud.html', locals())
    #Refresh member, to get new amount
    member = Member.objects.get(pk=member_id, active=True)
    return usermenu(request, room, member, product)

def ranks(request, year = None):
    if (year):
        return ranks_for_year(int(year))
    else:
        return ranks_for_year(next_fjule_party_year())

# renders stats for the year starting at first friday in december (year - 1) to the first friday in december (year)
# both at 10 o'clock
def ranks_for_year(year):
    if (year <= 1900 or year > 9999):
        return render(request, 'stregsystem/error_ranksnotfound.html', locals())
    milk = [2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 17, 18, 19, 20, 24, 25, 43, 44, 45 ]
    caffeine = [11, 12, 30, 32, 34, 35, 36, 37, 39, 1787, 1790, 1791, 1795, 1799, 1800, 1803]
    beer = [13, 14, 29, 42, 47, 54, 65, 66, 1773, 1776, 1777, 1779, 1780, 1783, 1793, 1794]
    
    FORMAT = '%d/%m/%Y kl. %H:%M'
    from_time = fjule_party(year - 1)
    to_time = fjule_party(year)
    kr_stat_list = sale_money_rank(from_time, to_time)
    beer_stat_list = sale_product_rank(beer, from_time, to_time)
    caffeine_stat_list = sale_product_rank(caffeine, from_time, to_time)
    milk_stat_list = sale_product_rank(milk, from_time, to_time)
    if not len(kr_stat_list) and not len(beer_stat_list) and not len(caffeine_stat_list) and not len(milk_stat_list):
        return render(request, 'stregsystem/error_ranksnotfound.html', locals())
    from_time_string = from_time.strftime(FORMAT)
    to_time_string = to_time.strftime(FORMAT)
    current_date = datetime.datetime.now()
    is_ongoing = current_date > from_time and current_date <= to_time
    return render(request, 'stregsystem/ranks.html', locals())
    
# gives a list of tuples (int_rank, string_username, int_value) of rankings of money spent between from_time and to_time.
#Limit is the maximum size of the returned list. 
def sale_money_rank(from_time, to_time, rank_limit=10):
    try:
        stat_list = map(lambda x, y: (y, x.username, money(x.sale__price__sum)), Member.objects.filter(active=True, sale__timestamp__gt = from_time, sale__timestamp__lte = to_time).annotate(Sum('sale__price')).order_by('-sale__price__sum', 'username')[:rank_limit], xrange(1, rank_limit+1))
    except:
        stat_list = {}
    return stat_list

# gives a list of tuples (int_rank, string_username, int_value) of rankings of sales of the specified products done between from_time and to_time.
#Limit is the maximum size of the returned list.
def sale_product_rank(ids, from_time, to_time, rank_limit=10):
    try:
        query = reduce(lambda x, y: x | y, map(lambda z: Q(sale__product__id=z), ids))
        #query &= Q(active=True)
        query &= Q(sale__timestamp__gt = from_time)
        query &= Q(sale__timestamp__lte = to_time)
        stat_list = map(lambda x, y: (y, x.username, x.sale__count), Member.objects.filter(query).annotate(Count('sale')).order_by('-sale__count', 'username')[:rank_limit], xrange(1,rank_limit+1))
    except:
        stat_list = {}
    return stat_list

#year of the last fjuleparty
def last_fjule_party_year():
    current_date = datetime.datetime.now()
    fjule_party_this_year = fjule_party(current_date.year)
    if current_date > fjule_party_this_year:
        return current_date.year
    return current_date.year - 1

#year of the next fjuleparty
def next_fjule_party_year():
    current_date = datetime.datetime.now()
    fjule_party_this_year = fjule_party(current_date.year)
    if current_date <= fjule_party_this_year:
        return current_date.year
    return current_date.year + 1

#date of fjuleparty (first friday of december) for the given year at 10 o'clock
def fjule_party(year):
    first_december = datetime.datetime(year, 12, 1, 22)
    days_to_add = (11 - first_december.weekday()) % 7
    return first_december + datetime.timedelta(days = days_to_add)
    
def money(value):
    if value is None:
        value = 0
    return fpformat.fix(value/100.0,2)
