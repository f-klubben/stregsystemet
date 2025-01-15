import dredd_hooks as hooks
import json
from utils import update_query_parameter_values, update_dictionary_values

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


# https://dredd.org/en/latest/data-structures.html#transaction-object
@hooks.before_each
def replace_4xx_parameter_values(transaction):
    """
    It isn't possible to specify individual parameter example values for each response type in OpenAPI.
    To properly test the return value of not-found parameters, replace all parameters.
    """
    if transaction['expected']['statusCode'][0] == '4':
        new_path = update_query_parameter_values(transaction['fullPath'], not_found_parameter_values)
        print(f"Update endpoint path, from '{transaction['fullPath']}' to '{new_path}'")
        transaction['fullPath'] = new_path
        transaction['request']['uri'] = new_path


@hooks.before_each
def replace_body_in_post_requests(transaction):
    if transaction['expected']['statusCode'][0] == '4' and transaction['id'].startswith("POST"):
        body = json.loads(transaction['request']['body'])
        update_dictionary_values(body, not_found_parameter_values)

        transaction['request']['body'] = json.dumps(body)
