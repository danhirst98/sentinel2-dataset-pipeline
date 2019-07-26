#!/bin/bash

pip install -r requirements.txt
wget http://step.esa.int/downloads/7.0/installers/esa-snap_sentinel_unix_7_0.sh
sudo chmod u+x esa-snap_sentinel_unix_7_0.sh
./esa-snap_sentinel_unix_7_0.sh
