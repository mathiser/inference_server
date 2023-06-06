class TaskNotFoundException(Exception):
    @staticmethod
    def msg():
        return "Task not found"

class TaskOutputTarNotFoundException(Exception):
    pass

class ModelNotFoundException(Exception):
    @staticmethod
    def msg():
        return "Model not found"

class TaskTarPathExistsException(Exception):
    pass

class InsertTaskException(Exception):
    @staticmethod
    def msg():
        return "Exception when inserting task to database"

class TarFileMissingException(Exception):
    pass

class ContradictingTarFileException(Exception):
    pass

class ModelInitializationException(Exception):
    pass

class TaskInitializationException(Exception):
    pass

class ModelInsertionException(Exception):
    pass

class ModelMountPointMissingException(Exception):
    pass