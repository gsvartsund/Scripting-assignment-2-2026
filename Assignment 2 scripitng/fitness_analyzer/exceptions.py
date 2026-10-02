# Invalid data and unreadable files will be handled in a consistent format.
class InvalidIdentifierError(ValueError):
    def __init__(self, message, field=""):
        super().__init__(message)
        self.field = field

class InvalidRecordError(ValueError):
    def __init__(self, message, field=""):
        super().__init__(message)
        self.field = field

class DataFileError(Exception):
    pass
