class TaskNotFoundException(Exception):
    pass

class TaskOutputZipNotFoundException(Exception):
    pass

class ModelNotFoundException(Exception):
    pass

class TaskZipPathExistsException(Exception):
    pass

class InsertTaskException(Exception):
    pass

class ZipFileMissingException(Exception):
    pass

class ContradictingZipFileException(Exception):
    pass

class ModelInitializationException(Exception):
    pass

class TaskInitializationException(Exception):
    pass

class ModelInsertionException(Exception):
    pass

class ModelMountPointMissingException(Exception):
    pass