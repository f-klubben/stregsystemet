def update_replace_dict(original_dict: dict, replacement: dict) -> None:
  """
  Same as dict.update(...) but doesn't add new values.
  Modifies existing dict.
  """
  original_dict.update({k: v for k, v in replacement.items() if k in original_dict})


def update_get_parameters(url_string: str, update_parameters: dict) -> str:
  from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

  parsed_url = urlparse(url_string)

  qs_dict = parse_qs(parsed_url.query, keep_blank_values=True)
  qs_dict_flattened = {key: value[0] for key, value in qs_dict.items()}
  update_replace_dict(qs_dict_flattened, update_parameters)
  updated_qs = urlencode(qs_dict_flattened, doseq=False)

  parsed_url = parsed_url._replace(query=updated_qs)

  return str(urlunparse(parsed_url))