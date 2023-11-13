CC=python3
INSTALLER=pip
MODULES=yt-dlp validators discord-py-interactions cryptography loguru
PLAT=win-amd64

install:
	$(CC) -m $(INSTALLER) install --upgrade pip
	$(INSTALLER) install --upgrade setuptools wheel
	
	$(INSTALLER) install -U $(MODULES) 
uninstall:
	$(INSTALLER) uninstall $(MODULES)

env:
	source env/bin/activate
encode:
	python3 ShuaigaoDiscord/encrypt.py
run:
	python3 ShuaigaoDiscord/server.py
