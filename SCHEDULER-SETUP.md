# Windows Task Scheduler Setup — PC Deal Tracker

Follow these steps to schedule the deal tracker to run automatically every 12 hours.

## Steps

1. **Open Task Scheduler**
   - Press `Win + R`, type `taskschd.msc`, press Enter

2. **Create Basic Task**
   - In the right panel, click **Create Basic Task…**

3. **Name the task**
   - Name: `PC Deal Tracker`
   - Description: `Runs the PC deal tracking agent to find and verify used/refurb deals`
   - Click **Next**

4. **Set the trigger**
   - Select **Daily**
   - Click **Next**
   - Set start time to a convenient time (e.g., 8:00 AM)
   - Recur every **1** day
   - Click **Next**

5. **Set the action**
   - Select **Start a program**
   - Click **Next**
   - Program/script: `C:\dev\pc-deal-tracker\run-tracker.bat`
   - Start in: `C:\dev\pc-deal-tracker`
   - Click **Next**

6. **Finish**
   - Check **Open the Properties dialog** before clicking Finish
   - Click **Finish**

7. **Configure repeat every 12 hours**
   - In the Properties dialog, go to the **Triggers** tab
   - Edit the trigger
   - Check **Repeat task every:** and set to **12 hours**
   - Set **for a duration of:** `Indefinitely`
   - Click **OK**

8. **Conditions tab** (optional)
   - If running on a laptop: uncheck **Start the task only if the computer is on AC power**

9. **Settings tab**
   - Check **Run task as soon as possible after a scheduled start is missed**
   - Click **OK**

## Verifying It Works

- Right-click the task in Task Scheduler and choose **Run** to test it manually
- Check `C:\dev\pc-deal-tracker\tracker-log.txt` to confirm output is being written
- Check `C:\dev\pc-deal-tracker\deals.md` to confirm the tracker updated it
