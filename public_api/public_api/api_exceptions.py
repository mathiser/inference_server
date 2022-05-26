class NoZipAttachedException(Exception):
    pass

class TaskNotFoundException(Exception):
    pass

class ModelNotFoundException(Exception):
    pass

class TaskOutputNotReadyException(Exception):
    pass

class TaskPathCreationException(Exception):
    pass

class ModelPathCreationException(Exception):
    pass

class InvalidHumanReadableId(Exception):
    pass

class PostTaskException(Exception):
    pass

class TaskOutputZipNotFound(Exception):
    pass

class ZipFileMissingException(Exception):
    pass

class ZipFileShouldBeNoneException(Exception):
    pass