def cached_property(func):
    def wrapper(self):
        key = func.__name__

        if key in self.__dict__:
            return self.__dict__[key]

        value = func(self)

        self.__dict__[key] = value

        return value

    return property(wrapper)
