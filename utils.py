def check_keys(key, key_list):
    if key in key_list:
        return True
    else:
        print("{0} in mandatory".format(key))
        exit(1)


def add_base64decode(resource_string):
    stripped_string = ''.join(c for c in resource_string if c not in '{}$')
    base64decode_string = "base64decode({0})".format(stripped_string)
    return '${' + base64decode_string + '}'
