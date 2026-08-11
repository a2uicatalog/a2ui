// src/lib/weather.js — live weather data as a2uicatalog weather_now /
// weather_outlook atom blocks. Surface-agnostic: returns plain atom
// {component, ...props} objects, same shape decodeV1() produces from a
// stored payload, so both render-to-slack.js and render-to-teams.js can
// map/compile them identically to any other reading.
//
// Open-Meteo: free, no API key, geocoding + forecast both public endpoints.

const GEOCODE_URL = 'https://geocoding-api.open-meteo.com/v1/search';
const FORECAST_URL = 'https://api.open-meteo.com/v1/forecast';
const DAY_NAMES = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];

// WMO weather code -> the 5-bucket code a2uicatalog's weather atoms draw a
// glyph for (sun|partly|cloud|rain|storm) — see atoms/schema.yaml's
// weather_now/weather_outlook field docs for the exact bucket names.
function wmoToCode(wmo) {
  if (wmo === 0) return 'sun';
  if (wmo === 1 || wmo === 2) return 'partly';
  if (wmo === 3 || wmo === 45 || wmo === 48) return 'cloud';
  if ([51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 71, 73, 75, 77, 80, 81, 82, 85, 86].includes(wmo)) return 'rain';
  if (wmo === 95 || wmo === 96 || wmo === 99) return 'storm';
  return 'cloud';
}

async function geocode(city) {
  const url = `${GEOCODE_URL}?name=${encodeURIComponent(city)}&count=1&language=en&format=json`;
  const resp = await fetch(url);
  const json = await resp.json();
  const hit = json.results && json.results[0];
  if (!hit) return null;
  return { lat: hit.latitude, lon: hit.longitude, name: hit.name, country: hit.country_code, timezone: hit.timezone };
}

// Returns { blocks: [weather_now atom, weather_outlook atom] } or
// { error: string } — never throws, matching this codebase's "degrade with
// a visible reason" convention rather than an unhandled exception mid-command.
export async function fetchWeatherBlocks(city) {
  const loc = await geocode(city);
  if (!loc) return { error: `could not find a location named "${city}"` };

  const url = `${FORECAST_URL}?latitude=${loc.lat}&longitude=${loc.lon}` +
    '&current=temperature_2m,weather_code,relative_humidity_2m,wind_speed_10m,uv_index' +
    '&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max' +
    `&timezone=${encodeURIComponent(loc.timezone || 'auto')}&forecast_days=4`;
  let data;
  try {
    const resp = await fetch(url);
    data = await resp.json();
  } catch (e) {
    return { error: 'weather service unreachable: ' + ((e && e.message) || e) };
  }
  if (!data.current || !data.daily) return { error: 'weather service returned an unexpected response' };

  const now = data.current;
  const daily = data.daily;

  const weatherNow = {
    type: 'weather_now', component: 'weather_now',
    city_line: `${loc.name.toUpperCase()}${loc.country ? ' — ' + loc.country : ''}`,
    stamp: new Date().toUTCString().slice(0, 22),
    temp: Math.round(now.temperature_2m),
    condition: wmoToCode(now.weather_code).toUpperCase(),
    code: wmoToCode(now.weather_code),
    hi: Math.round(daily.temperature_2m_max[0]), lo: Math.round(daily.temperature_2m_min[0]),
    stats: [
      { value: `${daily.precipitation_probability_max[0]}%`, label: 'Precip' },
      { value: `${Math.round(now.wind_speed_10m)} km/h`, label: 'Wind' },
      { value: `${now.uv_index}`, label: 'UV' },
      { value: `${now.relative_humidity_2m}%`, label: 'Humidity' },
    ],
  };

  const outlookDays = [1, 2, 3].map((i) => ({
    label: DAY_NAMES[new Date(daily.time[i]).getUTCDay()],
    date: new Date(daily.time[i]).toUTCString().slice(5, 11),
    code: wmoToCode(daily.weather_code[i]),
    hi: Math.round(daily.temperature_2m_max[i]), lo: Math.round(daily.temperature_2m_min[i]),
    precip: daily.precipitation_probability_max[i],
  }));
  const weatherOutlook = {
    type: 'weather_outlook', component: 'weather_outlook',
    title: 'NEXT 3 DAYS — OUTLOOK', city: loc.name,
    scale: {
      min: Math.min(...outlookDays.map((d) => d.lo)) - 2,
      max: Math.max(...outlookDays.map((d) => d.hi)) + 2,
    },
    days: outlookDays,
  };

  return { blocks: [weatherNow, weatherOutlook], location: loc.name };
}
