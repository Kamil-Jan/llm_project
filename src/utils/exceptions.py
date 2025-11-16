class BaseError(Exception):
    pass


class ConfigurationError(BaseError):
    pass


class DatabaseError(BaseError):
    pass


class TelegramError(BaseError):
    pass


class CalendarError(BaseError):
    pass


class DateParsingError(BaseError):
    pass


class EventError(BaseError):
    pass


class PermissionError(BaseError):
    pass
