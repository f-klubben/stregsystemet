import dredd_hooks as hooks

"""
{
   "name":"/api/products/active_products > Gets dictionary of products that are active > 400 > text/html; charset=utf-8",
   "id":"GET (400) /api/products/active_products?room_id=10",
   "host":"127.0.0.1",
   "port":"8000",
   "request":{
      "method":"GET",
      "uri":"/api/products/active_products?room_id=10",
      "headers":{
         "Accept":"text/html; charset=utf-8",
         "User-Agent":"Dredd/14.1.0 (Linux 5.15.167.4-microsoft-standard-WSL2; x64)"
      },
      "body":""
   },
   "expected":{
      "headers":{
         "Content-Type":"text/html; charset=utf-8"
      },
      "body":"Room not found",
      "statusCode":"400"
   },
   "origin":{
      "filename":"/mnt/c/Users/kress/source/repos/f-klubben/stregsystemet/openapi/stregsystem.yaml",
      "apiName":"Stregsystem",
      "resourceGroupName":"",
      "resourceName":"/api/products/active_products",
      "actionName":"Gets dictionary of products that are active",
      "exampleName":"400 > text/html; charset=utf-8"
   },
   "fullPath":"/api/products/active_products?room_id=10",
   "protocol":"http:",
   "skip":false
}
"""

not_found_parameter_values = {
  'room_id': [1],
  'member_id': [1],
  'username': ["404_user"],
}

def update_get_parameters(url_string: str, update_parameters: dict) -> str:
  from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

  parsed_url = urlparse(url_string)

  qs_dict = parse_qs(parsed_url.query, keep_blank_values=True)
  qs_dict.update({k: v for k, v in update_parameters.items() if k in qs_dict})
  updated_qs = urlencode(qs_dict, doseq=True)

  parsed_url = parsed_url._replace(query=updated_qs)

  return str(urlunparse(parsed_url))

@hooks.before_each
def replace_400_parameter_values(transaction):
  if transaction['expected']['statusCode'][0] == '4':
    new_path = update_get_parameters(transaction['fullPath'], not_found_parameter_values)
    transaction['fullPath'] = new_path
    transaction['request']['uri'] = new_path
