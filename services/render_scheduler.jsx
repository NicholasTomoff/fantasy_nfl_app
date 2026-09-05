# file: scheduler / render_scheduler.json
# This file is not Python.It's an example for Render Scheduler setup:

/* Render Cron Job Example (in dashboard) */
{
    "name": "Run Weekly Fantasy Tasks",
        "schedule": "0 13 * * TUE",  // Tuesdays at 6am PT / 13 UTC
            "url": "https://your-backend-url.onrender.com/admin/run-weekly/1",
                "method": "POST"
}

// Update the week number each week manually or automate later