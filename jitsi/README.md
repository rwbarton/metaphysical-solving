Once you have a working self-hosted Jitsi,

1. copy `mod_muc_solvers.lua` to `/usr/share/jitsi-meet/prosody-plugins/`
2. in `/etc/prosody/conf.avail/<*YOURHOSTNAME*>.cfg.lua`, find the VirtualHost section for `<*YOURHOSTNAME*>` and at the end of the list of modules_enabled, add "muc_solvers";
3. Modify your nginx configuration to pass relevant requests to the prosody port on localhost (the solving server only actually talks to the json endpoint):  add just before the final catch-all location in `/etc/nginx/sites-available/<*YOURHOSTNAME*>.conf` 
```
location = /<*JSON_ENDPOINT_NAME*> {
        proxy_pass http://localhost:5280/room-census;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header Host j.metaphysicalplant.com;
        add_header Content-Type "application/json; charset=UTF-8";
        add_header 'Access-Control-Allow-Origin' '*';
    }
    location = /<*HUMAN_ENDPOINT_NAME*> {
        proxy_pass http://localhost:5280/readable;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header Host j.metaphysicalplant.com;
        add_header Content-Type "text/html; charset=UTF-8";
        add_header 'Access-Control-Allow-Origin' '*';
    }
    location = /<*HUMAN_ROOM_ENDPOINT_NAME*> {
        proxy_pass http://localhost:5280/readableRooms;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header Host j.metaphysicalplant.com;
        add_header Content-Type "text/html; charset=UTF-8";
        add_header 'Access-Control-Allow-Origin' '*';
    }
```
You will also need to make sure that the solving server's local_settings.py includes `JITSI_SERVER_URL=<*YOURHOSTNAME*>` and `JITSI_ROOMS_URL=<*JSON_ENDPOINT_NAME*>`
