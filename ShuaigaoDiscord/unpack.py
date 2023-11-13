import os
import tarfile

root = os.path.dirname(os.path.abspath(__file__))
for targz in os.listdir(os.path.join(root, "src", "packet")):
    dirs, name = os.path.splitext(targz)
    file = tarfile.open(os.path.join(root, "src", "packet", targz))
    file.extractall(os.path.join(root, "src", "tools", os.path.basename(name).split('.')[0]))
    file.close()
    

