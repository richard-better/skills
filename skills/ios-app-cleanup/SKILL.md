---
name: ios-app-cleanup
description: Bulk-uninstall apps from an iPhone paired with this Mac using `xcrun devicectl`. Builds a checklist page with App Store icons so the user can tick apps and paste the list back. Manual invoke only.
disable-model-invocation: true
---

# iOS App Cleanup

Delete many iPhone apps from a Mac in one go. The agent lists the apps, builds a
checklist page, the user ticks what to remove and pastes the list back, and the agent
uninstalls and verifies.

## Requirements

- macOS with Xcode installed (for `xcrun devicectl`).
- iPhone paired with the Mac (USB once, then Wi-Fi works) and **Developer Mode on**:
  Settings > Privacy & Security > Developer Mode, then restart the phone.
- `python3` and `curl`.

## Steps

```bash
# 1. Find the device
xcrun devicectl list devices

# 2. List every app (the default only shows developer builds)
xcrun devicectl device info apps --device <UDID> --include-all-apps \
  --json-output /tmp/apps.json -q

# 3. Build the checklist page and open it
python3 -I scripts/build_app_page.py /tmp/apps.json /tmp/app-icons /tmp/apps.html "<device name>"
open /tmp/apps.html

# 4. User ticks apps, presses "Copy N apps", pastes the list back. Then:
xcrun devicectl device uninstall app --device <UDID> <bundle.id>   # loop over the list

# 5. Verify: re-run step 2 and check none of the bundle IDs remain
```

## UI

`scripts/build_app_page.py` turns the `devicectl` JSON into one self-contained HTML file:

- A grid of cards, one per removable app: icon, name, bundle ID, checkbox. Third-party
  apps first, removable Apple apps (`com.apple.*`) in their own section.
- Icons come from the public App Store lookup API (`itunes.apple.com/lookup?bundleId=a,b,c`),
  tried across several storefronts so regional apps are found. Apps not on the store get a
  letter placeholder.
- Toolbar: search (name or bundle ID), **Selected only**, **Select visible**, **Clear**, and
  **Copy N apps**, which copies a paste-ready prompt:
  `Please uninstall these N apps from <device>:` followed by `- Name (bundle.id)` lines.
  If clipboard access is blocked, the text opens in a dialog instead.
- Ticks persist in `localStorage`, so the page can be rebuilt and reloaded without losing them.
- Follows light and dark mode. `--embed` links icons instead of inlining them and uses host
  theme variables, for inline HTML viewers with size limits.

## Caveats

- **Confirm before deleting.** Uninstalling deletes the app's data on the phone. Warn about
  apps holding their own secrets (authenticators like Authy) and only act on an explicit list.
- **"The developer disk image could not be mounted" (error 12040)** means Developer Mode is off.
- **Restoring from backup:** apps only appear in `info apps` once installed. The count grows
  as the restore runs; rebuild the page when it is done.
- **Xcode and sideloaded builds** (dev, staging, AltStore apps) do not come back from a restore.
  Work-managed (MDM) apps may not either.
- **App Store apps uninstall fine** through `devicectl`, not just developer builds. Removable
  Apple apps can be removed too and reinstalled from the App Store.
- **Privacy:** icon lookup sends the bundle IDs to Apple's App Store API.
- The script fetches with `curl` because some Python builds (mise, python.org) can't find
  the system CA certificates for `urllib`.
- Pages with inlined icons are a few MB. Open them in a browser rather than pasting into an
  inline renderer.
