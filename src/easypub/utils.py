import easypub


def cached_property(func):
    def wrapper(self):
        key = func.__name__

        if key in self.__dict__:
            return self.__dict__[key]

        value = func(self)

        self.__dict__[key] = value

        return value

    return property(wrapper)


def get_client_ip(request):
    if easypub.config.debug:
        return request.client.host or "127.0.0.1"

    return request.headers["cf-connecting-ip"]
