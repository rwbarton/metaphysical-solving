#!/bin/bash

# Script to set up a puzzle Zulip server nicely.
# After setting up a new Zulip server, copy this script to the Zulip server
# in a directory writable by the zulip user, adjust the settings to taste
# and then run the script as user zulip. Finally copy puzzle-zulip.tar.gz
# to the solving server and unpack it as root under /etc/puzzle.


set -eufx

# Output settings
PUZZLE_REALM=metaphysicalplant.com
PUZZLE_REALM_NAME="Metaphysical Plant Zulip"
PUZZLE_ADMIN=metaphysicalplantserver@gmail.com # Make sure this doesn't have any funny characters
PUZZLE_ADMIN_NAME="Metaphysical Plant Server"

PUZZLE_STREAMS="plant,status"	# comma-separated

STATUS_AVATAR_URL='https://dl.dropboxusercontent.com/sh/o6lnsz6n9zacobq/AAA7kNmEbOwbxUF-m4Q9sOeBa/plant-icon-64.png'

# Zulip settings
ZULIP_SERVER=http://localhost:9991
#ZULIP_SERVER=https://zulip.metaphysicalplant.com
MANAGE=/srv/zulip/manage.py
#MANAGE=/home/zulip/deployments/current/manage.py



set -o pipefail

# First, set up the realm and an admin and get the admin's API key.
# create_realm can't create an invite-only realm (yet),
# so make it a non-open realm for now instead.
"$MANAGE" create_realm --domain "$PUZZLE_REALM" --name "$PUZZLE_REALM_NAME"
"$MANAGE" create_user --this-user-has-accepted-the-tos --domain "$PUZZLE_REALM" "$PUZZLE_ADMIN" "$PUZZLE_ADMIN_NAME"
"$MANAGE" knight "$PUZZLE_ADMIN" -f

# Terrible hack to extract API key
export PUZZLE_ADMIN
PUZZLE_API_KEY=$(echo '
import os
from zerver.models import UserProfile
print "\napi_key=" + UserProfile.objects.get(email=os.environ["PUZZLE_ADMIN"]).api_key + "\n"
' | "$MANAGE" shell | grep '^api_key=' | cut -d '=' -f 2)

# Now use the API to fix everything
PUZZLE_AUTH="$PUZZLE_ADMIN:$PUZZLE_API_KEY"
api () {
    if [ $1 = '--output' ]; then key=$2; shift 2; else key=; fi
    method=$1; shift
    path=$1; shift
    curl --silent -X "$method" "$ZULIP_SERVER/api/v1/$path" -u "$PUZZLE_AUTH" "$@" |
	python -c '
import sys
import json
resp = json.load(sys.stdin)
if resp["result"] != "success":
    sys.exit(1)
key = sys.argv[1]
if key and key in resp:
    print resp[key]
' "$key"
}

# Set realm attributes
api PATCH realm -d invite_required=true
api PATCH realm -d restricted_to_domain=false

# Adjust streams
api DELETE streams/engineering
api DELETE streams/social

# Create the new default streams
api POST users/me/subscriptions -d subscriptions="$(
    echo "$PUZZLE_STREAMS" |
	python -c 'import sys; import json; print json.dumps([{"name": s} for s in sys.stdin.read().split(",")])')"

"$MANAGE" set_default_streams --domain="$PUZZLE_REALM" --streams="$PUZZLE_STREAMS"

# Create bots
LOGGER_API_KEY=$(api --output api_key POST bots -d full_name="Logger Bot" -d short_name="logger")
STATUS_API_KEY=$(curl "$STATUS_AVATAR_URL" | api --output api_key POST bots -F full_name="Status Bot" -F short_name="status" -F filedata=@-)

# Increase status bot rate limit (more terrible hacks)
export STATUS_BOT_EMAIL="status-bot@$PUZZLE_REALM"
echo '
import os
import zerver.models
zerver.models.UserProfile.objects.get(email=os.environ["STATUS_BOT_EMAIL"]).rate_limit = "1:100"
' | "$MANAGE" shell

# Write output
mkdir zulip

cat >zulip/b+logger.conf <<EOF
[api]
key=$LOGGER_API_KEY
email=logger-bot@$PUZZLE_REALM
site=$ZULIP_SERVER
EOF

cat >zulip/b+status.conf <<EOF
[api]
key=$STATUS_API_KEY
email=status-bot@$PUZZLE_REALM
site=$ZULIP_SERVER
EOF

cat >zulip/create.json <<EOF
{"email":   "$PUZZLE_ADMIN",
 "api_key": "$PUZZLE_API_KEY"}
EOF

tar czvf puzzle-zulip.tar.gz zulip
rm -rf zulip

set +x

echo 
echo "All done! Copy puzzle-zulip.tar.gz to your solving server"
echo "and unpack it in the /etc/puzzle directory."
