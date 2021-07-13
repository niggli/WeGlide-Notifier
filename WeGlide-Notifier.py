######################################################################################
# WeGlide-Notifier.py
# Checks Weglide.org for new flights according to sets of user-defined filter 
# criteria, and sends pushover.net notifications if new flights are posted.
######################################################################################

# 27.4.21 very first draft, working but not very pretty

import requests
import json
import datetime
import subprocess

def printToLogfile(logstring) :
    dateObjectNow = datetime.datetime.now()
    timeString = dateObjectNow.isoformat()
    print(timeString + ": " + logstring)

# Load configuration from JSON file
with open('config.json') as configFile:
    config = json.load(configFile)

# Load list of known flights from JSON file
try :
    with open('knownflights.json') as flightsFile:
        knownFlights = json.load(flightsFile)
except FileNotFoundError :
    knownFlights = []

# Loop through all defined sources
for source in config["sources"] :
    printToLogfile("Source: " + source["name"])
    # Build payload
    payload = source["filtercriteria"]
    today = datetime.datetime.now()
    past = today - datetime.timedelta(days=config["general"]["daysback"])
    payload["scoring_date_start"] = past.strftime("%Y-%m-%d")
    payload["scoring_date_end"] = today.strftime("%Y-%m-%d")
    
    resp = requests.get(config["general"]["baseURL"], params=payload)
    datastore = resp.json()
    #print(resp.url)
    #print(datastore)
    #print(json.dumps(datastore, indent=4, sort_keys=True))

    #Check if new flights, loop through them
    for flight in datastore :
        if flight["id"] not in knownFlights:
            print (flight["id"])

            #Build message for notification
            flightURL = "https://weglide.org/flight/" + str(flight["id"])
            flightDate = (datetime.datetime.strptime(flight["scoring_date"], "%Y-%m-%d")).strftime("%d.%m.")         
            notificationMessage = flight["user"]["name"] + " hat einen Flug auf WeGlide hochgeladen: <a href="
            notificationMessage = notificationMessage + flightURL + ">"
            notificationMessage = notificationMessage + str(flight["contest"]["distance"]) + "km am " + flightDate + " aus " + flight["takeoff_airport"]["name"] + "</a>"

            #Correct or add flight in Vereinsflieger
            if "Weglide2Vereinsflieger_URL" in source :
                printToLogfile("Weglide2Vereinsflieger URL configured")

                #Get flight detail to read registration
                resp_detail = requests.get(config["general"]["detailsURL"]+ str(flight["id"]))
                datastore_detail = resp_detail.json()
                print(datastore_detail)

                #Build payload for Weglide2Vereinsflieger call
                callsign = datastore_detail["registration"]
                airfield = flight["takeoff_airport"]["name"]
                starttime = flight["takeoff_time"]
                landingtime = flight["landing_time"]
                pilotname = flight["user"]["name"]
                url = source["Weglide2Vereinsflieger_URL"]

                print(callsign)
                print(airfield)
                print(starttime)
                print(landingtime)
                print(pilotname)
                print(url)

                subprocess.call(["php", "-f", url, starttime, landingtime, pilotname, airfield, callsign])


            #Send notifications
            #Loop through all destinations
            for destination in config["destinations"] :
                #If the current source is active for this destination
                if source["source_id"] in destination["source_ids"] :
                    print("Send notification to " + destination["name"] + ": " + notificationMessage)
                    r = requests.post("https://api.pushover.net/1/messages.json", data = {
                        "token": config["general"]["apptoken"],
                        "user": destination["pushover_id"],
                        "html": "1",
                        "url" : flightURL,
                        "message": notificationMessage
                    })
                    #print(r.text)

            # Store in list of known flights
            knownFlights.append(flight["id"])

# When all sources have been worked, write list of known flights to file
with open('knownflights.json', 'w') as outfile:
    json.dump(knownFlights, outfile)


            
