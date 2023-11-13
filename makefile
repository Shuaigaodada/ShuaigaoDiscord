CC=python3
INSTALLER=pip
MODULES=yt-dlp validators discord-py-interactions
PLAT=win-amd64

install:
	$(CC) -m $(INSTALLER) install --upgrade pip
	$(INSTALLER) install --upgrade setuptools wheel
	
	$(INSTALLER) install -U $(MODULES) 
uninstall:
	$(INSTALLER) uninstall $(MODULES)

	
