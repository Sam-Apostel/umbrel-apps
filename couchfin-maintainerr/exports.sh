# Zero-touch wiring: read the API keys the official Sonarr, Radarr and Seerr
# (app id "jellyseerr") apps generated, so the configurator can connect
# Maintainerr to them without the owner pasting anything. Same approach as the
# official Prowlarr app, which reads ${UMBREL_ROOT}/app-data/<app>/data/...
#
# umbrelOS sources this file with `set -euo pipefail`, so every step that may
# fail is guarded and a missing file simply yields an empty value.

couchfin_maintainerr_data_root() {
  local app="${1}"
  local root=""
  # umbrelOS 2.0 can move an app's data folder; prefer its real location.
  root="$(printf '%s' "${SCRIPT_APP_DATA_ROOTS:-}" | jq --raw-output --arg app "${app}" '.[$app] // empty' 2>/dev/null)" || root=""
  if [[ -z "${root}" ]]; then
    root="${UMBREL_ROOT}/app-data/${app}/data"
  fi
  printf '%s' "${root}"
}

couchfin_maintainerr_arr_api_key() {
  local file=""
  file="$(couchfin_maintainerr_data_root "${1}")/config/config.xml"
  if [[ -f "${file}" ]]; then
    sed -n 's:.*<ApiKey>\([^<]*\)</ApiKey>.*:\1:p' "${file}" 2>/dev/null | head -n 1 || true
  fi
}

couchfin_maintainerr_seerr_api_key() {
  local file=""
  file="$(couchfin_maintainerr_data_root jellyseerr)/config/settings.json"
  if [[ -f "${file}" ]]; then
    jq --raw-output '.main.apiKey // empty' "${file}" 2>/dev/null || true
  fi
}

export APP_COUCHFIN_MAINTAINERR_SONARR_API_KEY="$(couchfin_maintainerr_arr_api_key sonarr)"
export APP_COUCHFIN_MAINTAINERR_RADARR_API_KEY="$(couchfin_maintainerr_arr_api_key radarr)"
export APP_COUCHFIN_MAINTAINERR_SEERR_API_KEY="$(couchfin_maintainerr_seerr_api_key)"
