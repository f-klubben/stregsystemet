import dredd_hooks as hooks

not_found_parameter_values = {
  'room_id': [1],
  'member_id': [1],
  'username': ["404_user"],
}

skipped_endpoints = [
  "GET (400) /api/member/payment/qr?username=kresten" # Skipped: test can't be implemented properly in OpenAPI
]

@hooks.before_each
def skip_endpoint(transaction):
  if transaction['id'] in skipped_endpoints:
    print(f"Skipping endpoint: {transaction['id']}")
    transaction['skip'] = True


def update_get_parameters(url_string: str, update_parameters: dict) -> str:
  from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

  parsed_url = urlparse(url_string)

  qs_dict = parse_qs(parsed_url.query, keep_blank_values=True)
  qs_dict.update({k: v for k, v in update_parameters.items() if k in qs_dict})
  updated_qs = urlencode(qs_dict, doseq=True)

  parsed_url = parsed_url._replace(query=updated_qs)

  return str(urlunparse(parsed_url))

# https://dredd.org/en/latest/data-structures.html#transaction-object
@hooks.before_each
def replace_4xx_parameter_values(transaction):
  """
  It isn't possible to specify individual parameter example values for each response type in OpenAPI.
  To properly test the return value of not-found parameters, replace all parameters.
  """
  if transaction['expected']['statusCode'][0] == '4':
    new_path = update_get_parameters(transaction['fullPath'], not_found_parameter_values)
    transaction['fullPath'] = new_path
    transaction['request']['uri'] = new_path
