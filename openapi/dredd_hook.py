import dredd_hooks as hooks
import json

not_found_parameter_values = {
  'room_id': 1,
  'member_id': 1,
  'username': "404_user",
}

skipped_endpoints = [
  "GET (400) /api/member/payment/qr?username=kresten" # Skipped: test can't be implemented properly in OpenAPI
]

@hooks.before_each
def skip_endpoint(transaction):
  if transaction['id'] in skipped_endpoints:
    print(f"Skipping endpoint: {transaction['id']}")
    transaction['skip'] = True


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


# https://dredd.org/en/latest/data-structures.html#transaction-object
@hooks.before_each
def replace_4xx_parameter_values(transaction):
  """
  It isn't possible to specify individual parameter example values for each response type in OpenAPI.
  To properly test the return value of not-found parameters, replace all parameters.
  """
  if transaction['expected']['statusCode'][0] == '4':
    new_path = update_get_parameters(transaction['fullPath'], not_found_parameter_values)
    print(f"Update endpoint path, from '{transaction['fullPath']}' to '{new_path}'")
    transaction['fullPath'] = new_path
    transaction['request']['uri'] = new_path


@hooks.before_each
def replace_body_in_post_requests(transaction):
  if transaction['expected']['statusCode'][0] == '4' and transaction['id'].startswith("POST"):
    body = json.loads(transaction['request']['body'])
    update_replace_dict(body, not_found_parameter_values)

    transaction['request']['body'] = json.dumps(body)
