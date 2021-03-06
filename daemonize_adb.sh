#!/bin/bash

SERVICE_NAME=adb-server
UPSTART_CONF_DIR=/etc/init
GROUP=`id -gn $USER`
ADB=`which adb`
LOGDIR=~/logs
mkdir -p $LOGDIR
LOGFILE=${LOGDIR}/${SERVICE_NAME}.log

echo "Trying to create service \"$SERVICE_NAME\"..."
if [ -f ${UPSTART_CONF_DIR}/${SERVICE_NAME}.conf ]
then
    echo "Service with such name already exists. Change SERVICE_NAME in $0"
    exit 1
fi

sudo -E bash << EOF
echo "description \"adb-server daemon\"
setuid $USER
setgid $GROUP
start on runlevel [2345]
stop on runlevel [06]

script
    $ADB kill-server >> $LOGFILE 2>&1
    $ADB -a fork-server server >> $LOGFILE 2>&1
end script

respawn
respawn limit 10 90" > ${UPSTART_CONF_DIR}/${SERVICE_NAME}.conf

[ $? == 0 ] || exit 1
echo "Service \"$SERVICE_NAME\" successfully created"
EOF
