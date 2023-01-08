-- provides an http endpoint at /room-census that reports list of rooms with the
-- number of members and created date in this JSON format:
--
--     {
--         "room_census": [
--             {
--                 "room_name": "<muc name>",
--                 "participants": <# participants>,
--                 "created_time": <unix timestamp>,
--             },
--             ...
--         ]
--     }
-- 
-- to activate, add "muc_census" to the modules_enabled table in prosody.cfg.lua
-- 
-- warning: this module is unprotected and intended for server admin use only.
-- when enabled, make sure to secure the endpoint at the web server or via
-- network filters

local jid = require "util.jid";
local json = require "util.json";
local iterators = require "util.iterators";
local util = module:require "util";
local is_healthcheck_room = util.is_healthcheck_room;

local have_async = pcall(require, "util.async");
if not have_async then
    module:log("error", "requires a version of Prosody with util.async");
    return;
end

local async_handler_wrapper = module:require "util".async_handler_wrapper;

local tostring = tostring;

-- required parameter for custom muc component prefix, defaults to "conference"
local muc_domain_prefix = module:get_option_string("muc_mapper_domain_prefix", "conference");

function convertRoomToLinkString(room_name)
    name = string.match(room_name,"^[^@]*")
    puzzleName = string.match(name,"^[^-]*")
    linkAddr = name
    retStr = "<a href=\""..linkAddr.."\" target=\"_blank\">"..puzzleName.."</a>"
    return retStr
end

function getRooms(host_session)
    room_data = {}
    for room in host_session.modules.muc.each_room() do
        if not is_healthcheck_room(room.jid) then
            local occupants = room._occupants;
	    local arr = {}
            if occupants then
		  for _, occupant in room:each_occupant() do
                        if string.sub(occupant.nick,-string.len("/focus"))~="/focus" then
                            for _, pr in occupant:each_session() do
                                local nick = pr:get_child_text("nick", "http://jabber.org/protocol/nick") or "";
		      		table.insert(arr,tostring(nick))
			    end
			end
		  end
		  else
                participant_count = 0
            end
            table.insert(room_data, {
                room_name = room.jid;
                participants = arr;
            });
        end
    end
    return room_data
end

--- handles request to get number of participants in all rooms
-- @return GET response
function handle_get_room_census(event)
    local host_session = prosody.hosts[muc_domain_prefix .. "." .. tostring(module.host)]
    if not host_session or not host_session.modules.muc then
        return { status_code = 400; }
    end

    room_data = {}
    for room in host_session.modules.muc.each_room() do
        if not is_healthcheck_room(room.jid) then
            local occupants = room._occupants;
	    local arr = {}
            if occupants then
--                participant_count = iterators.count(room:each_occupant()) - 1; -- subtract focus
		  for _, occupant in room:each_occupant() do
                        if string.sub(occupant.nick,-string.len("/focus"))~="/focus" then
                            for _, pr in occupant:each_session() do
                                local nick = pr:get_child_text("nick", "http://jabber.org/protocol/nick") or "";
		      		table.insert(arr,tostring(nick))
			    end
			end
		  end
		  else
                participant_count = 0
            end
            table.insert(room_data, {
                room_name = room.jid;
                participants = arr;
            });
        end
    end

    census_resp = json.encode({
        room_census = room_data;
    });
    return { status_code = 200; body = census_resp }
end

-- @return GET response
function handle_get_readable(event)
    local host_session = prosody.hosts[muc_domain_prefix .. "." .. tostring(module.host)]
    if not host_session or not host_session.modules.muc then
        return { status_code = 400; }
    end
    x = getRooms(host_session)

    roster = {}
    for _, roomRec in pairs(x) do
    	linkStr = convertRoomToLinkString(roomRec.room_name)
	for _, p in pairs(roomRec.participants) do
	    if roster[p] then
	       roster[p] = roster[p]..", "..linkStr
	    else
	       roster[p] = linkStr
	    end
	end
    end

    sortedParticipants = {}
    for participant, _ in pairs(roster) do table.insert(sortedParticipants,participant) end
    table.sort(sortedParticipants)
    	
    htmlresp = "<html><head><title>Plants Online</title></head><body><table>"
    if (#sortedParticipants)>0 then
        for _,participant in ipairs(sortedParticipants) do
    		htmlresp = htmlresp.."<tr><td><b>"..participant.."</b></td><td>"..roster[participant].."</td></tr>"
    	end
    else
	htmlresp = htmlresp.."<tr><td><i>No rooms in use</i></td></tr>"
    end
    htmlresp = htmlresp.."</table></body></html>"
    return { status_code = 200; body = htmlresp}
end

-- @return GET response
function handle_get_readable_rooms(event)
    local host_session = prosody.hosts[muc_domain_prefix .. "." .. tostring(module.host)]
    if not host_session or not host_session.modules.muc then
        return { status_code = 400; }
    end
    x = getRooms(host_session)


    	
    htmlresp = "<html><head><title>Plants Online</title></head><body><table>"
    sortedRooms = {}
    rosters = {}
    for _, roomRec in pairs(x) do
       	 linkStr = convertRoomToLinkString(roomRec.room_name)
	 table.insert(sortedRooms,linkStr)
   	 sortedParticipants = roomRec.participants
--    	 for participant, _ in pairs(roomRec.participants) do table.insert(sortedParticipants,participant) end
    	 table.sort(sortedParticipants)
	 rosters[linkStr]= "<tr><td>"..linkStr.."</td><td>"
	for _, p in ipairs(sortedParticipants) do
	    rosters[linkStr] = rosters[linkStr]..p..", "
	end
	rosters[linkStr] = string.sub(rosters[linkStr],1,-3).."</td></tr>"
    end
    table.sort(sortedRooms)

    for _,room in ipairs(sortedRooms) do
    	htmlresp = htmlresp..rosters[room]
    end
    htmlresp = htmlresp.."</table></body></html>"
    return { status_code = 200; body = htmlresp}
end


function module.load()
    module:depends("http");
        module:provides("http", {
                default_path = "/";
                route = {
                        ["GET room-census"] = function (event) return async_handler_wrapper(event,handle_get_room_census) end;
		        ["GET readable"] = function (event) return async_handler_wrapper(event,handle_get_readable) end;
			["GET readableRooms"] = function (event) return async_handler_wrapper(event,handle_get_readable_rooms) end;
                };
        });
end
