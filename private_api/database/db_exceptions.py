class TaskNotFoundException(Exception):
    @staticmethod
    def msg():
        return "Task not found"

class TaskOutputZipNotFoundException(Exception):
    pass

class ModelNotFoundException(Exception):
    @staticmethod
    def msg():
        return "Model not found"

class TaskZipPathExistsException(Exception):
    pass

class InsertTaskException(Exception):
    @staticmethod
    def msg():
        return "Exception when inserting task to database"

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