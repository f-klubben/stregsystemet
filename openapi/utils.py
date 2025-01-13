from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def update_dictionary_values(original: dict[Any, Any], replacement: dict[Any, Any]) -> None:
    """
    Same as dict.update(...) but doesn't add new keys.
    Mutates 'original'
    :param original: The dictionary to mutate.
    :param replacement: The dictionary with values to update the original with.
    """
    original.update({k: v for k, v in replacement.items() if k in original})


def update_query_parameter_values(url_string: str, new_parameter_values: dict[str, Any]) -> str:
    """
    Updates query parameters with new parameter values from new_parameter_values.
    :param url_string: The URL path of which to modify query parameters.
    :param new_parameter_values: The dictionary with new query parameter values.
    :return: The URL with updated query parameter.
    """
    parsed_url = urlparse(url_string)

    qs_dict = parse_qs(parsed_url.query, keep_blank_values=True)
    qs_dict_flattened = {key: value[0] for key, value in qs_dict.items()}
    update_dictionary_values(qs_dict_flattened, new_parameter_values)
    updated_qs = urlencode(qs_dict_flattened, doseq=False)

    parsed_url = parsed_url._replace(query=updated_qs)

    return str(urlunparse(parsed_url))
