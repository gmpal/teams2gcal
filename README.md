# Teams2GCal
### The Problem: Why your Teams Calendar is broken in Google
If you have ever tried to subscribe to a Microsoft Teams (or Outlook) calendar inside Google Calendar, you have likely noticed a frustrating bug: **All your events shift**

This happens because Microsoft often tells Google an event is in "Eastern Time" (or your local zone), but **fails to include the technical definition** of what "Eastern Time" actually is (the daylight savings rules, offsets, etc.). Google Calendar, being strict, sees an undefined timezone, panics, and defaults to UTC—shifting your 2:00 PM meeting to 9:00 AM.

### What this code does
This script acts as a "Man-in-the-Middle" helper to fix that data loss.

1.  **It intercepts the request:** Instead of Google asking Microsoft for the calendar directly, Google asks this little web app.
2.  **It fetches the data:** The app downloads the original `.ics` file from Microsoft.
3.  **It detects the error:** It scans the file for timezone labels (like `TZID:Eastern Time`) that are being used but haven't been defined.
4.  **It patches the file:** It injects the missing `VTIMEZONE` block (the standard code block that tells calendars how to handle daylight savings).
5.  **It delivers the fix:** It sends the repaired calendar file back to Google.

Google accepts the file, reads the new definition, and finally displays your meetings at the correct time.

---

### How to host this yourself (for free)
You don't need to be a developer to run this. You can get your own private link running in about 5 minutes using a free GitHub account and a free Render.com account.

#### Step 1: Fork the Code
#### Step 2: Deploy to Render
1.  Create a free account at [Render.com](https://render.com).
2.  Click **"New +"** and select **"Web Service"**.
3.  Connect your GitHub account and select the repository you just forked.
4.  Scroll down to the settings:
    *   **Runtime:** Python 3
    *   **Start Command:** `gunicorn app:app`
5.  Click **"Create Web Service"**.

#### Step 3: Get your fixed link
Once Render finishes (it takes about 2 minutes), it will give you a URL like `https://my-cal-fixer.onrender.com`.

To fix your calendar, take your original Microsoft ICS link and append it to your new URL like this:

```
https://my-cal-fixer.onrender.com/?ics_url=https://original-microsoft-link...
```

Paste **that** new link into Google Calendar, and your times will be correct.
