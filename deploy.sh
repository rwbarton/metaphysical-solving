#!/bin/sh -xe

if [ puzzle != $(whoami) ]; then
    exec sudo -u puzzle "$0" "$*"
fi

cd /home/puzzle/metaphysical-solving
git pull
. env/bin/activate
yes yes | python manage.py collectstatic # sigh
touch solving/wsgi.py
