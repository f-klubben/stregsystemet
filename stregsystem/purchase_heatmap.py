from typing import List

from stregsystem.models import Product, Member, Category
from datetime import datetime, timedelta


def __get_purchase_heatmap_day_color(
    products: List[Product],
    products_by_color: (
        List[Product],
        List[Product],
        List[Product],
    ),
    max_items_day: int,
) -> (int, int, int,):
    category_representation = [0, 0, 0]

    for product in products:
        for category_products_index in range(3):
            if product in products_by_color[category_products_index]:
                category_representation[category_products_index] = category_representation[category_products_index] + 1

    total_category_sum = sum(category_representation)

    brightness = total_category_sum / max_items_day

    if total_category_sum == 0:
        return 235, 237, 240  # Grey

    return tuple(category_sum / total_category_sum * 255 * brightness for category_sum in category_representation)


def __get_purchase_heatmap_data(
    member: Member,
    end_date: datetime,
    weeks_to_display: int,
    category_name_color: (
        str,
        str,
        str,
    ),
) -> list:
    days_to_go_back = (7 * weeks_to_display) - (6 - end_date.weekday() - 1)
    cutoff_date = end_date.date() - timedelta(days=days_to_go_back)
    last_sale_list = iter(
        member.sale_set.filter(timestamp__gte=cutoff_date, timestamp__lte=end_date).order_by('-timestamp')
    )

    products_by_day = []
    dates_by_day = []

    try:
        next_sale = next(last_sale_list)
        next_sale_date = next_sale.timestamp.date()
    except StopIteration:
        next_sale = None
        next_sale_date = None
        pass

    max_day_items = 0

    for single_date in (end_date - timedelta(days=n) for n in range(days_to_go_back)):
        products_by_day.append([])
        dates_by_day.append(single_date.date())

        try:
            while next_sale_date == single_date.date():
                products_by_day[-1].append(next_sale.product)

                next_sale = next(last_sale_list)
                next_sale_date = next_sale.timestamp.date()
        except StopIteration:
            next_sale = None
            next_sale_date = None

        max_day_items = max(max_day_items, len(products_by_day[-1]))

    category_by_name = [Category.objects.filter(name=cat_name) for cat_name in category_name_color]
    products_by_category = tuple(
        Product.objects.filter(categories__in=category_ins) for category_ins in category_by_name
    )

    # Proposed format:
    # Returned list: [<<Day 0 (today)>>, <<Day 1 (yesterday)>>, ...]
    # Day item: (<<Date>>, <<RGB values tuple-format>>, [<<item ID 1>>, ...])
    days = []

    for day_index in range(len(products_by_day)):
        day_color = __get_purchase_heatmap_day_color(products_by_day[day_index], products_by_category, max_day_items)
        days.append((dates_by_day[day_index], day_color, [x.id for x in products_by_day[day_index]]))

    return days

