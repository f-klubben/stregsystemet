import regex


class QuickBuyError(Exception):
    def __init__(self, parsed_part, failed_part):
        self.parsed_part = parsed_part
        self.failed_part = failed_part

class QuickBuyParseError(Exception):
    pass

_item_matcher = regex.compile(
    r'(?V1)(?P<productId>\d+)(?::(?P<count>\d+))?$'
)

def get_token_indexes(string, start_index):
    start, end = (-1, -1)
    # Get start
    for i in range(start_index, len(string)):
        if string[i] != " " and string[i] != "\t":
            start = i
            break
    else:
        return start, end
    # Get end
    for i in range(start, len(string)):
        if string[i] == " " or string[i] == "\t":
            end = i
            break
    else:
        # Set to one-past-end
        end = i + 1
    return start, end

def parse(buy_string):
    return username(buy_string, 0)

def username(buy_string, start_index):
    start, end = get_token_indexes(buy_string, start_index)
    if start == -1:
        raise QuickBuyError(buy_string[0: start_index], buy_string[start_index: len(buy_string)])
    username = buy_string[start: end]

    # Parse items
    product_lists = []
    while end != len(buy_string):
        prev_start, prev_end = start, end
        start, end = get_token_indexes(buy_string, end)
        if start == -1:
            raise QuickBuyError(buy_string[0: prev_end],
                                buy_string[prev_end: len(buy_string)])
        try:
            product_lists.append(item(buy_string[start: end]))
        except QuickBuyParseError:
            raise QuickBuyError(buy_string[0: start], buy_string[start: len(buy_string)])

    return username, [product for product_list in product_lists for product in product_list]

def item(token):
    match = _item_matcher.fullmatch(token)
    if match:
        return [int(match.group('productId'))] * (
            int(match.group('count') or 1))
    else:
        raise QuickBuyParseError
