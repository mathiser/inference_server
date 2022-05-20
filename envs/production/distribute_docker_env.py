import os
import shutil
shutil.copy2("docker-compose.yaml", "../../")
shutil.copy2(".env", "../../")
for d in os.listdir("../.."):
    if os.path.isdir(d):
        shutil.copy2(".env", d)