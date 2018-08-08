injection_url = ""
request_method = "GET"
post_params = {
}
cookies = ""
headers = {

}
proxies = {
    'http': 'http://127.0.0.1:8080',
    'https': 'http://127.0.0.1:8080',
}

# proxies = None

parameter_needs_quote = False
single_quote_allowed = True

truth_check = "RESPONSE_HEADER" # options are 'RESPONSE_HEADER', 'STATUS_CODE', and "CONTENT_STRING'
truth_string = "" # string to check in response when truth_check = "CONTENT_STRING"
truth_status = 302 # status of response to check when truth_check = "STATUS_CODE"
truth_response_header_name = "Location" # header name to check in response when truth_check = "RESPONSE_HEADER"
truth_response_header_value = "main.php" # header value to truth_response_header_name to check in response when truth_check = "RESPONSE_HEADER"
