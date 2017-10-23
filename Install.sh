# ---------------------------------------------------------------------------- #
# Installation script to setup the environment for py7slib                     #
# Author: Felipe Torres González (ftorres<AT>sevensols.com)                    #
# Date: 2016-02-03                                                             #
# ---------------------------------------------------------------------------- #
#!/bin/bash
echo "\033[1mConfiguring py7slib environment...\033[0m"
rm lib/libetherbone.so.1.0
rm lib/libetherbone.so
rm bin/eb-discover
arch=$(uname -m)
version=$(ls ./lib/ | grep $arch | grep -oh "[0-9].*" | cut -d"_" -f1)
ln bin/eb-discover_$arch bin/eb-discover 2> /dev/null
ln lib/libetherbone.so.${version}_$arch lib/libetherbone.so.${version} 2> /dev/null
ln lib/libetherbone.so.${version} lib/libetherbone.so 2> /dev/null
# Stablish location of py7slib folder
echo "path=\"`pwd`\"" > scripts/__path__.py
