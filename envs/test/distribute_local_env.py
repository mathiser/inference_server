import os
import shutil
shutil.copy2("docker-compose.yaml", "../../")
shutil.copy2(".env", "../../")
for d in os.listdir("../.."):
    if os.path.isdir(d):
        dst = os.path.join("../../", d, ".env")
        if os.path.isfile(dst):
            os.remove(dst)
        shutil.copy2(".env", dst)