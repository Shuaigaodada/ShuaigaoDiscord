CC=python3
INSTALLER=pip
MODULES=yt-dlp validators discord-py-interactions cryptography loguru discord.py-interactions[voice] validators
TOOLS=aria2c
PLAT=win-amd64
SERVERS=ShuaigaoDiscord/src/servers

install:
	$(CC) -m $(INSTALLER) install --upgrade pip
	$(INSTALLER) install --upgrade setuptools wheel
	
	$(INSTALLER) install -U $(MODULES) 
	sudo apt-get install $(TOOLS)
uninstall:
	$(INSTALLER) uninstall $(MODULES)

env:
	source env/bin/activate
encode:
	python3 ShuaigaoDiscord/encrypt.py
run:
	python3 ShuaigaoDiscord/server.py
test:
	python3 tests/engine_test.py
unpack:
	python3 ShuaigaoDiscord/unpack.py
clean:
	rm -rf ${SERVERS}
