# ESO Encounter Log Fixer — v1.0
**By @SixteenthMatt**

A lightweight desktop utility to repair raw ESO encounter logs by replacing missing anonymous player entries with accurate @gamertags and character names using Class, Race, and CP fingerprints.

---

### Windows SmartScreen Notice
Because this is a custom-compiled community executable without an expensive commercial signing certificate, Windows Defender / SmartScreen will likely show a blue popup on first launch:
1. Click **More info**.
2. Click **Run anyway**.

---

### How to Record Logs in ESO (Xbox on PC)
1. **Start Logging:** Type `/encounterlog` in chat before pull. A confirmation message will appear in the chatbox.
2. **Stop Logging:** Type `/encounterlog` again once the trial is finished.
3. **Default File Location:**
    `Documents\Elder Scrolls Online\pccert\Logs\Encounter.log`
    (Or `...\Elder Scrolls Online\live\Logs\Encounter.log` depending on your launcher/PC version)

---

### Pro-Tip Before You Raid
Take a screenshot of your group roster right before pulling the first boss. Having a quick visual reference of everyone's Gamertag, Class, and starting CP makes configuring the fixer take under a minute.

---

### How to Use the Fixer
1. **Input Log:** Click **Browse...** and select your raw `Encounter.log`.
2. **Roster Setup:** Click **Auto-Detect Full Roster** to scan initial fingerprints, then replace the placeholder names with the real `@Gamertag` for each player:
   * **Format:** `@Gamertag Class CP`
   * **Examples:** `@MainTank Necromancer 2087` or `@Heals 4 2484`
3. **Patch Log:** Click **Fix & Patch Log**. The repaired file is saved alongside the original as `Encounter_fixed.log`.

---

### Uploading to ESO Logs
1. Head to [ESO Logs](https://www.esologs.com/).
2. Open the **ESO Logs Uploader** desktop app.
3. Select and upload your newly created `Encounter_fixed.log`.

*(Provided AS-IS for guild runs. Use at your own risk.)*
