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
    products_by_color: Tuple[List[int], List[int], List[int]]
    max_items_day: int

    def __init__(self, max_items_day: int, products_by_color: Tuple[List[int], List[int], List[int]]):
        self.max_items_day = max_items_day
        self.products_by_color = products_by_color
        super().__init__(mode_name="ColorCategorized", mode_description="Med kategorier")

    def get_day_color(self, products: List[Product]) -> Tuple[int, int, int]:
        category_representation = [0, 0, 0]

        for product in products:
            for category_products_index in range(3):
                if product.id in self.products_by_color[category_products_index]:
                    category_representation[category_products_index] = (
                        category_representation[category_products_index] + 1
                    )

        total_category_sum = sum(category_representation)

        if total_category_sum == 0:
            return 235, 237, 240  # Grey

        red = 70 + (category_representation[0] / total_category_sum) * 185
        green = 70 + (category_representation[1] / total_category_sum) * 185
        blue = 70 + (category_representation[2] / total_category_sum) * 185

        return red, green, blue

    def get_day_summary(self, products: List[Product]) -> str:
        return f"{len(products)} {'vare' if len(products) == 1 else 'varer'} købt"

    @staticmethod
    def get_products_by_categories(category_name_color: Tuple[str, str, str]) -> Tuple[List[int], List[int], List[int]]:
        return tuple(
            Category.objects.filter(name=category).values_list("product", flat=True) for category in category_name_color
        )


class ItemCountHeatmapColorMode(HeatmapColorMode):
    max_items_day: int

    def __init__(self, max_items_day: int):
        self.max_items_day = max_items_day
        super().__init__(mode_name="ItemCount", mode_description="Antal")

    def get_day_color(self, products: List[Product]) -> Tuple[int, int, int]:
        if len(products) == 0 or self.max_items_day == 0:
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
        if len(products) == 0 or self.max_money_day_oere == 0:
            return 235, 237, 240  # Grey

        day_sum = sum(p.price for p in products)
        lerp_value = day_sum / self.max_money_day_oere

        return lerp_color((255, 255, 200), (255, 255, 0), lerp_value)  # Lightyellow - Yellow

    def get_day_summary(self, products: List[Product]) -> str:
        return f"{money(sum(p.price for p in products))} 𝓕$ brugt"

    @staticmethod
    def get_products_money_sum(day_list: List[Tuple[date, List[Product]]]) -> int:
        max_product_sum = 0

        for day_date, product_list in day_list:
            max_product_sum = max(max_product_sum, sum(product.price for product in product_list))

        return max_product_sum


def prepare_heatmap_template_context(member: Member, weeks_to_display: int, end_date: datetime.date) -> dict:
    """Prepares the context required to successfully load purchase_heatmap.html rendering template."""
    __raw_heatmap_data = __get_heatmap_data_by_date(member, end_date, weeks_to_display)

    __products_in_color_categories = ColorCategorizedHeatmapColorMode.get_products_by_categories(
        ("Øl", "Energidrik", "Sodavand")
    )

    __max_items_bought = ItemCountHeatmapColorMode.get_max_product_count(__raw_heatmap_data)

    # Default heatmap modes.
    heatmap_modes = [
        ItemCountHeatmapColorMode(__max_items_bought),
        MoneySumHeatmapColorMode(MoneySumHeatmapColorMode.get_products_money_sum(__raw_heatmap_data)),
        ColorCategorizedHeatmapColorMode(__max_items_bought, __products_in_color_categories),
    ]
    __reorganized_heatmap_data = __convert_purchase_data_to_heatmap_day(__raw_heatmap_data, heatmap_modes)

    column_labels, rows = get_heatmap_graph_data(weeks_to_display, __reorganized_heatmap_data, end_date)

    return {"column_labels": column_labels, "rows": rows, "heatmap_modes": heatmap_modes}


def get_heatmap_graph_data(
    weeks_to_display: int, heatmap_data: List[HeatmapDay], end_date: datetime.date
) -> (List[str], List[Tuple[str, HeatmapDay]]):
    reorganized_heatmap_data = __organize_heatmap_data_by_weekdays(heatmap_data[::-1])

    row_labels = ["", "Mandag", "", "Onsdag", "", "Fredag", ""]
    rows = zip(row_labels, reorganized_heatmap_data)

    column_labels = [str((end_date - timedelta(days=7 * x)).isocalendar()[1]) for x in range(weeks_to_display)][::-1]

    return column_labels, rows


def __convert_purchase_data_to_heatmap_day(
    products_by_date: List[Tuple[date, List[Product]]], heatmap_modes: List[HeatmapColorMode]
) -> List[HeatmapDay]:
    days = []

    for day_index in range(len(products_by_date)):
        day_date, product_list = products_by_date[day_index]
        day_colors = [color_mode.get_day_color(product_list) for color_mode in heatmap_modes]
        day_summaries = [color_mode.get_day_summary(product_list) for color_mode in heatmap_modes]

        days.append(HeatmapDay(day_date, [product.id for product in product_list], day_colors, day_summaries))

    return days


def __get_heatmap_data_by_date(
    member: Member,
    end_date: datetime.date,
    weeks_to_display: int,
) -> List[Tuple[date, List[Product]]]:
    days_to_go_back = (7 * weeks_to_display) - (6 - end_date.weekday() - 1)
    cutoff_date = end_date - timedelta(days=days_to_go_back)

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
        dates_by_day.append(single_date)

        while sale_index < len(last_sale_list) and last_sale_list[sale_index].timestamp.date() == single_date:
            products_by_day[-1].append(last_sale_list[sale_index].product)
            sale_index += 1

    return list(zip(dates_by_day, products_by_day))


def __organize_heatmap_data_by_weekdays(heatmap_data: list) -> list:
    # Transforms [<<Day 0 (today)>>, <<Day 1 (yesterday)>>, ...]
    # into
    # [
    #   [<<Day - last monday>>, <<Day - the monday before that>>, ...],
    #   [<<Day - last tuesday>>, <<Day - the tuesday before that>>, ...],
    # ...]
    new_list = [[] for _ in range(7)]
    for i in range(len(heatmap_data)):
        new_list[i % 7].append(heatmap_data[i])

    return new_list


def lerp_color(color1: Tuple[int, int, int], color2: Tuple[int, int, int], value: float) -> Tuple[int, int, int]:
    """Linearly interpolate between two 3-dimensional tuples."""
    return (
        int(color1[0] + (color2[0] - color1[0]) * value),
        int(color1[1] + (color2[1] - color1[1]) * value),
        int(color1[2] + (color2[2] - color1[2]) * value),
    )
