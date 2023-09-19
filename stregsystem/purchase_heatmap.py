from typing import List, NamedTuple, Tuple

from stregsystem.models import Product, Member, Category
from datetime import datetime, timedelta, date

from stregsystem.templatetags.stregsystem_extras import money


class HeatmapDay(NamedTuple):
    date: datetime.date
    products: List[int]
    color: List[Tuple[int, int, int]]
    summary: List[str]


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

    def get_day_summary(self, products: List[Product]) -> str:
        """Returns a summary of the day, e.g. amount of money used, or product count."""
        pass


class ColorCategorizedHeatmapColorMode(HeatmapColorMode):
    products_by_color: Tuple[List[Product], List[Product], List[Product]]
    max_items_day: int

    def __init__(self, max_items_day: int, products_by_color: Tuple[List[Product], List[Product], List[Product]]):
        self.max_items_day = max_items_day
        self.products_by_color = products_by_color
        super().__init__(mode_name="ColorCategorized", mode_description="Med kategorier")

    def get_day_color(self, products: List[Product]) -> Tuple[int, int, int]:
        category_representation = [0, 0, 0]

        for product in products:
            for category_products_index in range(3):
                if product in self.products_by_color[category_products_index]:
                    category_representation[category_products_index] = (
                        category_representation[category_products_index] + 1
                    )

        total_category_sum = sum(category_representation)

        if total_category_sum == 0:
            return 235, 237, 240  # Grey

        brightness = total_category_sum / self.max_items_day

        return tuple(
            ((category_sum / total_category_sum) * 255) for category_sum in category_representation
        )

    def get_day_summary(self, products: List[Product]) -> str:
        return f"{len(products)} {'vare' if len(products) == 1 else 'varer'} købt"

    @staticmethod
    def get_category_objects(category_name_color: str) -> List[Product]:
        category = Category.objects.filter(name=category_name_color)
        return Product.objects.filter(categories__in=category)


class ItemCountHeatmapColorMode(HeatmapColorMode):
    max_items_day: int

    def __init__(self, max_items_day: int):
        self.max_items_day = max_items_day
        super().__init__(mode_name="ItemCount", mode_description="Antal")

    def get_day_color(self, products: List[Product]) -> Tuple[int, int, int]:
        if len(products) == 0:
            return 235, 237, 240  # Grey

        lerp_value = len(products) / self.max_items_day

        return lerp_color((144, 238, 144), (0, 100, 0), lerp_value)  # Lightgreen - Darkgreen

    def get_day_summary(self, products: List[Product]) -> str:
        return f"{len(products)} {'vare' if len(products) == 1 else 'varer'} købt"

    @staticmethod
    def get_max_product_count(day_list: List[Tuple[date, List[Product]]]) -> int:
        max_day_items = 0

        for day_date, product_list in day_list:
            max_day_items = max(max_day_items, len(product_list))

        return max_day_items


class MoneySumHeatmapColorMode(HeatmapColorMode):
    max_money_day_oere: int

    def __init__(self, max_money_day_oere: int):
        self.max_money_day_oere = max_money_day_oere
        super().__init__(mode_name="MoneySum", mode_description="Penge brugt")

    def get_day_color(self, products: List[Product]) -> Tuple[int, int, int]:
        if len(products) == 0:
            return 235, 237, 240  # Grey

        day_sum = sum(p.price for p in products)
        lerp_value = day_sum / self.max_money_day_oere

        return lerp_color((255, 255, 200), (255, 255, 0), lerp_value)  # Lightyellow - Yellow

    def get_day_summary(self, products: List[Product]) -> str:
        return f"{money(sum(p.price for p in products))} F$ brugt"

    @staticmethod
    def get_products_money_sum(day_list: List[Tuple[date, List[Product]]]) -> int:
        max_product_sum = 0

        for day_date, product_list in day_list:
            max_product_sum = max(max_product_sum, sum(product.price for product in product_list))

        return max_product_sum


def prepare_heatmap_template_context(member: Member, weeks_to_display: int) -> dict:
    __raw_heatmap_data = get_purchase_data_ordered_by_date(member, datetime.today(), weeks_to_display)

    __products_in_color_categories = tuple(
        ColorCategorizedHeatmapColorMode.get_category_objects(category_name)
        for category_name in ("beer", "energy", "soda")
    )

    __max_items_bought = ItemCountHeatmapColorMode.get_max_product_count(__raw_heatmap_data)

    # Default heatmap modes.
    heatmap_modes = [
        ItemCountHeatmapColorMode(__max_items_bought),
        MoneySumHeatmapColorMode(MoneySumHeatmapColorMode.get_products_money_sum(__raw_heatmap_data)),
        ColorCategorizedHeatmapColorMode(__max_items_bought, __products_in_color_categories),
    ]
    __reorganized_heatmap_data = convert_purchase_data_to_heatmap_day(__raw_heatmap_data, heatmap_modes)

    column_labels, rows = get_heatmap_graph_data(weeks_to_display, __reorganized_heatmap_data)

    return {"column_labels": column_labels, "rows": rows, "heatmap_modes": heatmap_modes}


def get_heatmap_graph_data(
    weeks_to_display: int, heatmap_data: List[HeatmapDay]
) -> (List[str], List[Tuple[str, HeatmapDay]]):
    current_date = date.today()
    reorganized_heatmap_data = __organize_purchase_heatmap_data(heatmap_data[::-1], current_date)
    row_labels = ["", "Mandag", "", "Onsdag", "", "Fredag", ""]
    column_labels = [str((current_date - timedelta(days=7 * x)).isocalendar()[1]) for x in range(weeks_to_display)][
        ::-1
    ]

    rows = zip(row_labels, reorganized_heatmap_data)

    return column_labels, rows


def convert_purchase_data_to_heatmap_day(
    products_by_date: List[Tuple[date, List[Product]]], heatmap_modes: List[HeatmapColorMode]
) -> List[HeatmapDay]:
    # Proposed format:
    # Returned list: [<<Day 0 (today)>>, <<Day 1 (yesterday)>>, ...]
    # Day item: (<<Date>>, [<<RGB values by mode>>], [<<item ID 1>>, ...])
    days = []

    for day_index in range(len(products_by_date)):
        day_date, product_list = products_by_date[day_index]
        day_colors = [color_mode.get_day_color(product_list) for color_mode in heatmap_modes]
        day_summaries = [color_mode.get_day_summary(product_list) for color_mode in heatmap_modes]

        days.append(HeatmapDay(day_date, [product.id for product in product_list], day_colors, day_summaries))

    return days


def get_purchase_data_ordered_by_date(
    member: Member,
    end_date: datetime,
    weeks_to_display: int,
) -> List[Tuple[date, List[Product]]]:
    days_to_go_back = (7 * weeks_to_display) - (6 - end_date.weekday() - 1)
    cutoff_date = end_date.date() - timedelta(days=days_to_go_back)

    last_sale_list = list(
        member.sale_set.filter(timestamp__gte=cutoff_date, timestamp__lte=end_date)
        .select_related('product')
        .order_by('-timestamp')
    )

    products_by_day = []
    dates_by_day = []

    sale_index = 0
    for single_date in (end_date - timedelta(days=n) for n in range(days_to_go_back)):
        products_by_day.append([])
        dates_by_day.append(single_date.date())

        while sale_index < len(last_sale_list) and last_sale_list[sale_index].timestamp.date() == single_date.date():
            products_by_day[-1].append(last_sale_list[sale_index].product)
            sale_index += 1

    return list(zip(dates_by_day, products_by_day))


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


def lerp_color(color1: Tuple[int, int, int], color2: Tuple[int, int, int], value: float) -> Tuple[int, int, int]:
    return (
        int(color1[0] + (color2[0] - color1[0]) * value),
        int(color1[1] + (color2[1] - color1[1]) * value),
        int(color1[2] + (color2[2] - color1[2]) * value),
    )
