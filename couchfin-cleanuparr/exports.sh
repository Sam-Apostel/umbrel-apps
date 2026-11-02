# Zero-touch wiring: read the API keys that the official Sonarr and Radarr
# apps generated, so the configurator can connect Cleanuparr to them without
# the owner pasting anything. Same approach as the official Prowlarr app,
# which reads ${UMBREL_ROOT}/app-data/<app>/data/config/config.xml.
#
# umbrelOS sources this file with `set -euo pipefail`, so every step that may
# fail is guarded and a missing file simply yields an empty value.

couchfin_cleanuparr_arr_api_key() {
  local app="${1}"
  local root=""
  # umbrelOS 2.0 can move an app's data folder; prefer its real location.
  root="$(printf '%s' "${SCRIPT_APP_DATA_ROOTS:-}" | jq --raw-output --arg app "${app}" '.[$app] // empty' 2>/dev/null)" || root=""
  if [[ -z "${root}" ]]; then
    root="${UMBREL_ROOT}/app-data/${app}/data"
  fi
  if [[ -f "${root}/config/config.xml" ]]; then
    sed -n 's:.*<ApiKey>\([^<]*\)</ApiKey>.*:\1:p' "${root}/config/config.xml" 2>/dev/null | head -n 1 || true
  fi
}

export APP_COUCHFIN_CLEANUPARR_SONARR_API_KEY="$(couchfin_cleanuparr_arr_api_key sonarr)"
export APP_COUCHFIN_CLEANUPARR_RADARR_API_KEY="$(couchfin_cleanuparr_arr_api_key radarr)"
