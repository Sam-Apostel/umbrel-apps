# Couchfin App Store for Umbrel

A small Umbrel community app store with companion apps for a media setup built from the
**official** Umbrel apps: Jellyfin, Seerr (app id `jellyseerr`), Sonarr, Radarr, Transmission
(and optionally Prowlarr), watched with Couchfin on Apple TV and iPhone.

| App | Version | What it fixes |
| --- | --- | --- |
| **Cleanuparr** (`couchfin-cleanuparr`) | 2.10.12 | Sonarr/Radarr sometimes grab a "release" that is really an `.iso`, `.exe` or archive. Cleanuparr removes it from Transmission, blocklists it in Sonarr/Radarr and searches for the next release, automatically. |
| **Maintainerr** (`couchfin-maintainerr`) | 3.31.0 | The SSD fills up. Maintainerr shows media everyone has watched in a "Leaving soon" collection and, once you allow it, deletes it through Radarr/Sonarr. |

Both apps connect themselves to your existing apps: they find them by their Umbrel container
names (`sonarr_server_1:8989`, `radarr_server_1:7878`, `transmission_server_1:9091`,
`jellyfin_server_1:8096`, `jellyseerr_server_1:5055`) and read the Sonarr, Radarr and Seerr API keys
from those apps' own config files. The only thing you paste is a Jellyfin API key into Maintainerr.

## Add the store to umbrelOS

1. Open the umbrelOS **App Store**.
2. Click the **⋯** button (top right) and choose **Community App Stores**.
3. Paste `https://github.com/sam-apostel/umbrel-apps` and click **Add**.
4. Open the **Couchfin App Store** and install the apps.

Sonarr, Radarr and Transmission (and Jellyfin for Maintainerr) must be installed first; umbrelOS
enforces this through the apps' `dependencies`.

## First run

### Cleanuparr: nothing to do

Install it and wait a minute. On first start a one-shot `configurator` container:

- creates the Cleanuparr login: user **`umbrel`**, password = the one umbrelOS shows on the app's page
  (it is generated per install; nothing is hard-coded),
- adds Sonarr, Radarr (API keys read from their `config.xml`) and Transmission,
- turns on the **Malware Blocker** with Cleanuparr's official
  [blacklist](https://github.com/Cleanuparr/Cleanuparr/blob/main/blacklist) (`.iso`, `.exe`, `.lnk`,
  archives, samples, ...). When nothing usable is left in a torrent, Cleanuparr removes it, blocklists
  it in the *arr and asks for a replacement search,
- turns on **failed-import strikes**: if Sonarr/Radarr can't import a finished download because it
  contains no usable video (`No files found are eligible for import`, `Sample`,
  `No audio tracks detected`, executable/dangerous file warnings), it gets a strike every 5 minutes and is
  removed, blocklisted and searched again after 3 strikes.

Private-tracker torrents are ignored. Cleanuparr's *proactive* search (hunting for upgrades) stays off,
so it never fills the disk by itself. Everything is editable in Cleanuparr afterwards; the
configurator only runs once and never overwrites your changes.

### Maintainerr: paste one Jellyfin key

1. In Jellyfin: **Dashboard → API Keys → +**, name it `Maintainerr`, copy the key.
2. In Maintainerr: **Settings → Jellyfin**, URL `http://jellyfin_server_1:8096`, paste the key, **Test**,
   **Save**.

Within a minute or two Couchfin adds one rule per Jellyfin library (named
`Leaving soon: <library>`). Sonarr, Radarr and Seerr are already connected. (Jellyfin keeps its API
keys in its database, so they can't be read safely from disk like the *arr keys.)

## Cleanup rules

A **movie** or a **TV season** is picked when **all** of these are true:

1. everyone in the household has watched it (every Jellyfin user that existed when the rule was
   created; for seasons, every episode),
2. the last time anyone watched it was at least **14 days** ago,
3. nobody marked it as a **favourite** (for seasons, the show isn't a favourite either),
4. seasons only: the season has **finished airing**,
5. the media disk is more than **80% full** (the rule stores "less than X GiB free", worked out from
   your disk size when the rule was created).

Picked media appears in the **Leaving soon** collection in Jellyfin/Couchfin. After **7 days** in the
collection Maintainerr acts on it, **through Radarr/Sonarr**: movies are unmonitored and their files
deleted, seasons are unmonitored and deleted (future seasons of an ongoing show still download), and the
**Seerr request is cleared** so it can be requested again later. If the disk drops below 80% again,
items leave the collection on the next rule run without being touched.

### Safe start: "Do nothing" mode

The rules are created with the action **Do nothing**: the collection fills up, but nothing is deleted.
Watch it for a week or two. When you're happy:

1. Maintainerr → **Rules** → edit `Leaving soon: <Movies library>` → **Action**: **Unmonitor and delete
   files** → Save.
2. Edit `Leaving soon: <Shows library>` → **Action**: **Unmonitor and delete season** → Save.

### Changing the rules

Everything is in Maintainerr → **Rules** → edit:

- **Household**: the `Viewed by` / `Users that watched every episode` rule holds the list of
  Jellyfin users. Remove guest accounts, add new family members.
- **14 days**: the `Last view date` / `Newest episode view date` rule.
- **80%**: the `Remaining disk space (GB)` rule (value in GiB, on `/downloads`).
- **7 days in "Leaving soon"**: the collection's "Take action after days".
- **Keep something forever**: mark it as a favourite in Jellyfin, or exclude it in Maintainerr.

The defaults used on first run live in `couchfin-maintainerr/docker-compose.yml`
(`DISK_USAGE_PERCENT`, `WATCHED_DAYS`, `LEAVING_SOON_DAYS`). They only matter before the rules exist.

## 4K on the Apple TV (manual, optional)

[Recyclarr](https://recyclarr.dev) is deliberately **not** included: it has no web UI (Umbrel apps
need one), and syncing TRaSH profiles into the existing Radarr risks changing existing profiles and
mass-upgrading the library, which is exactly how an SSD fills up. Adding one separate profile by hand
takes five minutes and never touches the existing ones. Based on the
[TRaSH guides](https://trash-guides.info/Radarr/radarr-setup-quality-profiles/):

1. **Radarr → Settings → Custom Formats**: import (from the
   [TRaSH JSON](https://trash-guides.info/Radarr/Radarr-collection-of-custom-formats/)) `HDR`,
   `DV Boost`, `HDR10+ Boost`, `BR-DISK`, `LQ`, `LQ (Release Title)`, `3D`, `Upscaled`, `Extras`,
   `x265 (no HDR/DV)`. New custom formats score 0 in your existing profiles, so they change nothing
   there.
2. **Settings → Profiles → +** named **UHD WEB**:
   - qualities: only **WEBDL-2160p** and **WEBRip-2160p** (no Remux, no Bluray-2160p, never BR-DISK),
     upgrade until WEBDL-2160p,
   - scores: `HDR` 500, `DV Boost` 1000, `HDR10+ Boost` 100; `BR-DISK`, `LQ`, `LQ (Release Title)`,
     `3D`, `Upscaled`, `Extras`, `x265 (no HDR/DV)` -10000,
   - minimum custom format score 0, upgrade until custom format score 1500.
3. Pick **UHD WEB** per movie on the movie's **Edit** page instead of changing existing movies in bulk.
   Do **not** change the default profile. (Seerr's separate 4K requests need a second Radarr instance,
   which this setup avoids.)

Why WEB only: streaming 4K WEB-DLs carry Dolby Vision profile 5 or 8 (with HDR10 fallback), which the
Apple TV plays; UHD Blu-ray/remux releases use DV profile 7, which the Apple TV can't play as Dolby
Vision, and they are 40-80 GB each. Radarr keeps one file per movie, so a movie on UHD WEB *replaces*
its 1080p file (expect 15-25 GB per film). Sonarr works the same way with a `UHD WEB` profile
(WEBDL-2160p/WEBRip-2160p).

## Maintenance

Images are pinned as `tag@sha256:digest`, so every update is a deliberate pull request that bumps
`version` in `umbrel-app.yml` and the image tag + digest in `docker-compose.yml` (both services of an
app use the same image). The CI workflow lints YAML, checks that app ids start with `couchfin-`, that
ports are unique and that every image is pinned.

## Troubleshooting

- **Cleanuparr shows the setup wizard / Sonarr is missing**: open the app's logs in umbrelOS and look at
  the `configurator` container. If Sonarr or Radarr had never started when Cleanuparr was installed,
  restart Cleanuparr once they have; the missing parts are added then.
- **Maintainerr has no rules**: check that Jellyfin is saved in Maintainerr's settings; the
  configurator log says what it is waiting for. If you already created your own rules, Couchfin leaves
  them alone.
