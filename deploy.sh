#!/bin/bash


EXEC_FILES=(
	daemon.py
	datamodel.py
	paradium.py
	stations.py
	)

for i in "${EXEC_FILES[@]}"
	do
		echo "copying "$i" to /opt/paradium ..."
		cp -a "$i" /opt/paradium
	done

echo "sync htdocs ..."
rsync -av htdocs /opt/paradium/


