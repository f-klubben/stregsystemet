from typing import List, NamedTuple, Tuple

from stregsystem.models import Product, Member, Category
from datetime import datetime, timedelta


class HeatmapDay(NamedTuple):
    date: datetime.date
    color: List[Tuple[int, int, int]]
    products: List[int]


class HeatmapColorMode(object):
    def __init__(self, mode_name: str, mode_description: str):
        # The ID to look up a description for in purchase_heatmap template.
        self.mode_name = mode_name

        # The text showing on the figure as link to switch to mode.
        self.mode_description = mode_description
        pass

    def get_day_color(self, products: List[Product]) -> Tuple[int, int, int]:
        """Returns the color of a particular day given the products bought on that day."""
        pass


class ColorCategorizedHeatmapColorMode(HeatmapColorMode):
    products_by_color: Tuple[List[Product], List[Product], List[Product]]
    max_items_day: int

    def __init__(self, products_by_color: Tuple[List[Product], List[Product], List[Product]], max_items_day: int):
        self.products_by_color = products_by_color
        self.max_items_day = max_items_day
        super().__init__(mode_name="ColorCategorized", mode_description="Med kategorier")

    @staticmethod
    def get_category_objects(category_name_color: str) -> List[Product]:
        category = Category.objects.filter(name=category_name_color)
        return Product.objects.filter(categories__in=category)

    def get_day_color(self, products: List[Product]) -> Tuple[int, int, int]:
        category_representation = [0, 0, 0]

        for product in products:
            for category_products_index in range(3):
                if product in self.products_by_color[category_products_index]:
                    category_representation[category_products_index] = category_representation[
                                                                           category_products_index] + 1

        total_category_sum = sum(category_representation)

        brightness = total_category_sum / self.max_items_day

        if total_category_sum == 0:
            return 235, 237, 240  # Grey

        return tuple(255 - (category_sum / total_category_sum * 255 * brightness) for category_sum in category_representation)


class ItemCountHeatmapColorMode(HeatmapColorMode):
    max_items_day: int

    def __init__(self, max_items_day: int):
        self.max_items_day = max_items_day
        super().__init__(mode_name="ItemCount", mode_description="General visning")

    def get_day_color(self, products: List[Product]):
        if len(products) == 0:
            return 235, 237, 240  # Grey

        return 0, int(255 - (255 * (len(products) / (self.max_items_day + 1)))), 0


class MoneySumHeatmapColorMode(HeatmapColorMode):
    # TODO: Finish class
    def __init__(self):
        super().__init__(mode_name="MoneySum", mode_description="Penge brugt")


def get_heatmap_graph_data(weeks_to_display: int, heatmap_data: List[HeatmapDay], heatmap_modes: List[HeatmapColorMode]) -> (List[str], List[Tuple[str, HeatmapDay]]):
    reorganized_heatmap_data = __organize_purchase_heatmap_data(heatmap_data[::-1], datetime.today())
    row_labels = ["", "Mandag", "", "Onsdag", "", "Fredag", ""]
    current_week = datetime.today().isocalendar()[1]
    column_labels = [str(current_week - x) for x in range(weeks_to_display)][::-1]

    rows = zip(row_labels, reorganized_heatmap_data)

    return column_labels, rows


def get_purchase_data_for_heatmap(
        member: Member,
        end_date: datetime,
        weeks_to_display: int,
        heatmap_modes: List[HeatmapColorMode]
) -> (List[HeatmapDay], int):

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

    # Proposed format:
    # Returned list: [<<Day 0 (today)>>, <<Day 1 (yesterday)>>, ...]
    # Day item: (<<Date>>, [<<RGB values by mode>>], [<<item ID 1>>, ...])
    days = []

    for day_index in range(len(products_by_day)):
        day_colors = [color_mode.get_day_color(products_by_day[day_index]) for color_mode in heatmap_modes]

        days.append(
            HeatmapDay(
                dates_by_day[day_index],
                day_colors,
                [product.id for product in products_by_day[day_index]],
            )
        )

    return days


def __organize_purchase_heatmap_data(heatmap_data: list, start_date: datetime.date) -> list:
    # Transforms [<<Day 0 (today)>>, <<Day 1 (yesterday)>>, ...]
    # into
    # [
    #   [<<Day - last monday>>, <<Day - the monday before that>>, ...],
    #   [<<Day - last tuesday>>, <<Day - the tuesday before that>>, ...],
    # ...]

    # TODO: Doesn't take current weekday into consideration. But still works?
    new_list = []
    for i in range(7):
        new_list.append([])
        for j in range(len(heatmap_data)):
            if j % 7 == i:
                new_list[i].append(heatmap_data[j])

    return new_list
