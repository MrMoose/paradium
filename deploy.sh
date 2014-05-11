#!/bin/bash


EXEC_FILES=(
	daemon.py
	datamodel.py
	paradium.py
	stations.py
	)

# make sure directory structure exists
if [ ! -d /opt/paradium ]; then
	mkdir -p /opt/paradium
fi
if [ ! -d /opt/paradium/scripts ]; then
	mkdir -p /opt/paradium/scripts
fi

for i in "${EXEC_FILES[@]}"
	do
		echo "copying "$i" to /opt/paradium ..."
		cp -a "$i" /opt/paradium
	done

echo "sync htdocs ..."
rsync -av htdocs /opt/paradium/

echo "copy udev start rule ..."
sudo cp -a ./udev/98-bluez-pulse.rules /etc/udev/rules.d/98-bluez-pulse.rules

echo "copy bluetooth autostart on connect script ..."
cp -a ./scripts/bluez-pulse-plugged /opt/paradium/scripts/bluez-pulse-plugged
chmod +x /opt/paradium/scripts/bluez-pulse-plugged

echo ".. all done!"

