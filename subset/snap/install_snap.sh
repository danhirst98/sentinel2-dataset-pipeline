#!/bin/bash

URL="http://step.esa.int/downloads/6.0/installers/esa-snap_sentinel_unix_6_0.sh"

wget -q $URL -O install_sentinel.sh

chmod +x install_sentinel.sh

./install_sentinel.sh -q -dir /app/snap/

# update snap to the latest versions
/app/snap/bin/snap --nosplash --nogui --modules --refresh
/app/snap/bin/snap --nosplash --nogui --modules --update-all

rm ./install_sentinel.sh
