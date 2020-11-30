def check_keys(key, key_list):
    if key in key_list:
        return True
    else:
        print("{0} in mandatory".format(key))
        return False