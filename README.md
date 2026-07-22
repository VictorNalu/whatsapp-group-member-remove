# WhatsApp Group Member Remove

A Python + Selenium script that automates removing all members from a WhatsApp group via [WhatsApp Web](https://web.whatsapp.com).

> ⚠️ **This script permanently removes people from a WhatsApp group.** There is no confirmation prompt and no dry-run mode — it will keep removing members until the list is empty or it hits an error. Read this whole README before running it. Removed members are **not** notified individually, but they will no longer be in the group, and re-adding them requires inviting each person again.

## What it does

1. Opens WhatsApp Web in an automated Chrome browser.
2. Waits for you to scan the QR code (or reuses a saved login session on later runs).
3. Searches for a group by name and opens it.
4. Opens the group's **Group Info** panel.
5. Repeatedly hovers over the first removable member, opens their options menu, and clicks **Remove** → confirms.
6. Stops automatically once the member list is empty, or after several consecutive errors in a row (as a safety net against getting stuck).

## Requirements

- Python 3.9+
- Google Chrome installed
- A WhatsApp account with **admin rights** in the group you want to clear (only admins can remove members)

## Setup

1. Clone this repo:
   ```bash
   git clone https://github.com/VictorNalu/whatsapp-group-member-remove.git
   cd whatsapp-group-member-remove
   ```

2. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```

3. Open `whatsapp-group-auto-member-remove.py` and set the group name near the top of the script:
   ```python
   group_name = "Your Group Name Here"
   ```
   This must match the group's name **exactly** as it appears in WhatsApp.

## Usage

```bash
python whatsapp-group-auto-member-remove.py
```

- A Chrome window will open and navigate to WhatsApp Web.
- **On the first run**, scan the QR code with your phone when prompted. This creates a local Chrome profile folder (in your home directory) so you won't need to re-scan on future runs.
- The script will then search for your group, open it, and start removing members automatically.
- **Watch the console output.** It prints progress for every step and every member removed, and will tell you if/why it stops early.

To stop the script at any time, press `Ctrl+C` in the terminal.

## Notes on reliability

WhatsApp Web's page structure changes periodically, and this script relies on specific element selectors (`data-testid` attributes) to find things like the search box, the group row, and the per-member options menu. If WhatsApp updates their UI, some selectors may need to be updated — the script saves debug screenshots and HTML snapshots (`whatsapp_debug_*.png` / `.html`) whenever it can't find something, which can help with troubleshooting.

**Do not commit or share these debug files** — they can contain real phone numbers, contact names, and message content from your account. The included `.gitignore` excludes them by default.

## Credits

This project builds on an original script shared by **Sagar Chauhan**, whose initial version laid the groundwork for automating WhatsApp group member removal with Selenium. Thanks to him for sharing that first version — this repo extends it with more resilient selectors, better error handling, and debug tooling for keeping up with WhatsApp Web's frequently changing UI.

## Disclaimer

This project is provided as-is, for personal/educational use with groups you administer. Automating actions on WhatsApp Web may be against WhatsApp's Terms of Service — use at your own risk. The author(s) are not responsible for any account restrictions, data loss, or unintended removals resulting from use of this script. Always double-check the group name and member list before running.

## License

MIT (or your preferred license — add a `LICENSE` file if you want this to be explicit)