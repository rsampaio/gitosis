import redis
from ConfigParser import RawConfigParser, NoSectionError, NoOptionError


class RedisConfigParser(RawConfigParser):

    def __init__(self, defaults={}, addr='127.0.0.1', namespace='gitosis'):
        self.redis = redis.Redis(addr)
        self.redis.select(1)
        self.namespace = namespace
        self.__sections_key__ = "%s:sections" % self.namespace
        self._defaults = defaults
        self._sections = self.sections()
    
    def sections(self):
        size = self.redis.llen(self.__sections_key__)
        return self.redis.lrange(self.__sections_key__, 0, size)

    def has_section(self, section):
        return section in self.sections()

    def add_section(self, section):
        hkey = "%s:section:%s" % (self.namespace, section)
        self.redis.lpush(self.__sections_key__, section)

    def remove_section(self, section):
        self.redis.lpop(self.section_key, section)

    def options(self, section):
        if self.has_section(section):
            hkey = "%s:section:%s:options" % (self.namespace, section)
            options = self.redis.lrange(hkey, 0, self.redis.llen(hkey))
            return options
        else:
            raise NoSectionError(section)

    def has_option(self, section, option):
        hkey = "%s:section:%s:option:%s" % (self.namespace, section, option)
        if self.has_section(section):
            if not self.redis.exists(hkey):
                raise NoOptionError(section, option)
        else:
            raise NoSectionError(section)
        return True
    
    def get(self, section, option):
        if self.has_option(section, option):
            hkey = "%s:section:%s:option:%s" % (self.namespace, section, option)
            value = self.redis.get(hkey)
            return value
        else:
            raise NoOptionError(section, option)

    def getboolean(self, section, option):
        if self.get(section, option) in ("false", "0", 0):
            return False
        elif self.get(section, option) in ("true", "1", 1):
            return True

    def getint(self, section, option):
        return int(self.get(section, option))

    def getfloat(self, section, option):
        return float(self.get(section, option))

    def items(self, section):
        return [(i, self.get(section, i)) for i in self.options(section)]

    def set(self, section, option, value):
        if self.has_section(section):
            hkey = "%s:section:%s:option:%s" % (self.namespace, section, option)
            self.redis.set(hkey, value)
        else:
            raise NoSectionError

