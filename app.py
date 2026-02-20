from flask import Flask, request, Response
import requests
import re

app = Flask(__name__)

# 1. Map Microsoft Windows names to IANA Standard names
TZ_MAPPING = {
    "Romance Standard Time": "Europe/Brussels",
    "W. Europe Standard Time": "Europe/Paris",
    "GMT Standard Time": "Europe/London",
    "Eastern Standard Time": "America/New_York",
    "Central European Standard Time": "Europe/Warsaw",
    "Morocco Standard Time": "Africa/Casablanca",
    "FLE Standard Time": "Europe/Kiev"
}

# 2. Define clean, standard VTIMEZONE blocks (Epoch 1970)
# These replace the broken Microsoft "1601" definitions.
STANDARD_VTIMEZONES = """
BEGIN:VTIMEZONE
TZID:Europe/Brussels
BEGIN:DAYLIGHT
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
TZNAME:CEST
DTSTART:19700329T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
TZNAME:CET
DTSTART:19701025T030000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
END:VTIMEZONE

BEGIN:VTIMEZONE
TZID:Europe/Paris
BEGIN:DAYLIGHT
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
TZNAME:CEST
DTSTART:19700329T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
TZNAME:CET
DTSTART:19701025T030000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
END:VTIMEZONE

BEGIN:VTIMEZONE
TZID:Europe/London
BEGIN:DAYLIGHT
TZOFFSETFROM:+0000
TZOFFSETTO:+0100
TZNAME:BST
DTSTART:19700329T010000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0100
TZOFFSETTO:+0000
TZNAME:GMT
DTSTART:19701025T020000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
END:VTIMEZONE

BEGIN:VTIMEZONE
TZID:America/New_York
BEGIN:DAYLIGHT
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT
DTSTART:19700308T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:EST
DTSTART:19701101T020000
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
END:STANDARD
END:VTIMEZONE

BEGIN:VTIMEZONE
TZID:Africa/Casablanca
BEGIN:STANDARD
TZOFFSETFROM:+0100
TZOFFSETTO:+0100
TZNAME:+01
DTSTART:19700101T000000
END:STANDARD
END:VTIMEZONE

BEGIN:VTIMEZONE
TZID:Europe/Kiev
BEGIN:DAYLIGHT
TZOFFSETFROM:+0200
TZOFFSETTO:+0300
TZNAME:EEST
DTSTART:19700329T030000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0300
TZOFFSETTO:+0200
TZNAME:EET
DTSTART:19701025T040000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
END:VTIMEZONE
"""

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

    # STEP 1: Remove the corrupted Microsoft VTIMEZONE blocks entirely.
    # We use Regex to find everything between BEGIN:VTIMEZONE and END:VTIMEZONE
    # flags=re.DOTALL makes the dot (.) match newlines.
    ics = re.sub(r'BEGIN:VTIMEZONE.*?END:VTIMEZONE', '', ics, flags=re.DOTALL)

    # STEP 2: Rename the Timezones inside the Events
    count = 0
    for ms_tz, iana_tz in TZ_MAPPING.items():
        if ms_tz in ics:
            # Replace TZID=Romance Standard Time with TZID=Europe/Brussels
            ics = ics.replace(f'TZID={ms_tz}', f'TZID={iana_tz}')
            count += 1

    # STEP 3: Strip Microsoft-specific junk properties Google Calendar doesn't need
    ics = re.sub(r'^X-MICROSOFT-[^\r\n]*\r?\n', '', ics, flags=re.MULTILINE)
    ics = re.sub(r'^X-MS-[^\r\n]*\r?\n', '', ics, flags=re.MULTILINE)

    # STEP 5: Inject the clean, standard VTIMEZONE definitions
    # We insert them right after the calendar starts
    if 'BEGIN:VCALENDAR' in ics:
        ics = ics.replace('BEGIN:VCALENDAR', 'BEGIN:VCALENDAR\n' + STANDARD_VTIMEZONES)

    # Clean up empty lines created by regex removal
    ics = re.sub(r'\n\s*\n', '\n', ics)

    print(f"Fixed {count} timezone references and injected standard definitions.")

    return Response(ics, mimetype='text/calendar')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)