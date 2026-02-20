from flask import Flask, request, Response
import requests

app = Flask(__name__)

# Map Microsoft Windows Timezones to IANA Timezones
TZ_MAPPING = {
    "Romance Standard Time": "Europe/Brussels",
    "W. Europe Standard Time": "Europe/Paris",
    "GMT Standard Time": "Europe/London",
    "Eastern Standard Time": "America/New_York",
    "Central European Standard Time": "Europe/Warsaw",
    "Fiji Standard Time": "Pacific/Fiji",
    "Central Standard Time": "America/Chicago",
    "Pacific Standard Time": "America/Los_Angeles",
    "Morocco Standard Time": "Africa/Casablanca",
    "FLE Standard Time": "Europe/Kiev"
}

@app.route('/', methods=['GET'])
def fix_ics():
    ics_url = request.args.get('ics_url')
    if not ics_url:
        return "Missing ?ics_url= parameter", 400

    try:
        r = requests.get(ics_url, timeout=30)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"Failed to fetch ICS: {str(e)}", 502
    
    ics = r.text

    count = 0
    for ms_tz, iana_tz in TZ_MAPPING.items():
        if ms_tz in ics:
            # 1. Fix the Event Reference (The meeting itself)
            # Looks like: DTSTART;TZID=Romance Standard Time:...
            ics = ics.replace(f'TZID={ms_tz}', f'TZID={iana_tz}')
            
            # 2. Fix the Definition Header (The rule that explains the time)
            # Looks like: TZID:Romance Standard Time
            ics = ics.replace(f'TZID:{ms_tz}', f'TZID:{iana_tz}')
            
            count += 1

    print(f"Fixed {count} timezone types (Events and Definitions).")

    return Response(ics, mimetype='text/calendar')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)