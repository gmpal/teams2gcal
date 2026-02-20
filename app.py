from flask import Flask, request, Response
import requests
import re

app = Flask(__name__)

VTIMEZONE_TEMPLATES = {
    "Eastern Time (US & Canada)": """BEGIN:VTIMEZONE
TZID:Eastern Time (US & Canada)
BEGIN:DAYLIGHT
DTSTART:19700308T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
END:DAYLIGHT
BEGIN:STANDARD
DTSTART:19701101T020000
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
END:STANDARD
END:VTIMEZONE""",
    # Add "Pacific Standard Time", "Central European Time", your local one, etc.
}

@app.route('/', methods=['GET'])
def fix_ics():
    ics_url = request.args.get('ics_url')
    if not ics_url:
        return "Missing ?ics_url= parameter", 400

    # Fetch original
    r = requests.get(ics_url, timeout=30)
    if r.status_code != 200:
        return f"Failed to fetch ICS: {r.status_code}", 502
    
    ics = r.text

    # Find all used TZIDs
    used_tzids = set(re.findall(r'TZID=([^:\r\n]+)', ics))

    # Append missing VTIMEZONE blocks at the end (before final END:VCALENDAR)
    added = False
    for tz in used_tzids:
        if tz in VTIMEZONE_TEMPLATES and f'TZID:{tz}' not in ics:
            ics = ics.replace('END:VCALENDAR', VTIMEZONE_TEMPLATES[tz] + '\nEND:VCALENDAR')
            added = True

    if added:
        print(f"Added VTIMEZONE blocks for: {used_tzids}")

    return Response(ics, mimetype='text/calendar')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)