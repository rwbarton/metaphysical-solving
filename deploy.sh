#!/bin/sh -xe

if [ puzzle != $(whoami) ]; then
    exec sudo -u puzzle "$0" "$*"
fi

cd /home/puzzle/solving
git pull
yes yes | python manage.py collectstatic # sigh
touch wsgi.py
