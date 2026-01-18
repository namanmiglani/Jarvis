const params = {
	latitude: 49.2593,
	longitude: -123.2475,
	hourly: ["temperature_2m", "precipitation_probability", "wind_speed_10m"],
	forecast_days: 1,
};
const url = `https://api.open-meteo.com/v1/forecast?latitude=${params.latitude}&longitude=${params.longitude}&hourly=${params.hourly.join(',')}&forecast_days=${params.forecast_days}`;

console.log('Starting weather fetch...');
const response = await fetch(url);
const data = await response.json();
console.log('Data fetched:', data);

// Attributes for timezone and location
const latitude = data.latitude;
const longitude = data.longitude;
const elevation = data.elevation;
const utcOffsetSeconds = data.utc_offset_seconds;

console.log(
	`\nCoordinates: ${latitude}°N ${longitude}°E`,
	`\nElevation: ${elevation}m asl`,
	`\nTimezone difference to GMT+0: ${utcOffsetSeconds}s`,
);


const hourly = data.hourly;

// Note: The order of weather variables in the URL query and the indices below need to match!
// Parse times robustly: API may return ISO strings or epoch seconds.
const weatherData = {
	hourly: {
		time: hourly.time.map(t => {
			if (typeof t === 'number') {
				// epoch seconds, apply offset if provided
				return new Date((t + (utcOffsetSeconds || 0)) * 1000);
			}
			// ISO-like string
			return new Date(t);
		}),
		temperature_2m: hourly.temperature_2m,
		precipitation_probability: hourly.precipitation_probability,
		wind_speed_10m: hourly.wind_speed_10m,
	},
};

// The 'weatherData' object now contains a simple structure, with arrays of datetimes and weather information
console.log("\nHourly data:\n", weatherData.hourly)

// New code: Update DOM with weather data
function getIcon(precip) {
    return precip > 0 ? '🌧️' : '☀️'; // Simple emoji based on precipitation
}

function formatTime(date) {
	if (!(date instanceof Date) || isNaN(date)) return '';
	return date.toLocaleTimeString([], { hour: 'numeric', hour12: true });
}

// Update current weather (first hour)
const currentTemp = weatherData.hourly.temperature_2m[0];
const currentPrecipProb = weatherData.hourly.precipitation_probability[0];
const currentWind = weatherData.hourly.wind_speed_10m[0];
document.getElementById('temp').textContent = `${Math.round(currentTemp)}°C`;
document.getElementById('precip').textContent = `${Math.round(currentPrecipProb)}% chance of rain`;
document.getElementById('wind').textContent = `${Math.round(currentWind)} km/h wind`;

// Visual selection based on temperature
// Thresholds: >=20°C => sunny, <20°C => cloudy (adjust as desired)
const sunEl = document.getElementById('sun');
const cloudEl = document.getElementById('cloud');
const cloudAreaEl = document.getElementById('cloud-area');
if (sunEl && cloudEl) {
	const hotThreshold = 20;
	if (currentTemp >= hotThreshold) {
		sunEl.classList.add('visible');
		cloudEl.classList.remove('visible');
		if (cloudAreaEl) cloudAreaEl.classList.remove('visible');
	} else {
		cloudEl.classList.add('visible');
		sunEl.classList.remove('visible');
		if (cloudAreaEl) cloudAreaEl.classList.add('visible');
	}
}

// Render next 5 hours (small stylistic row)
function renderNextHours(count = 5) {
	const container = document.getElementById('next-hours');
	if (!container) return;
	container.innerHTML = '';
	const times = weatherData.hourly.time;
	const temps = weatherData.hourly.temperature_2m;

	for (let i = 1; i <= count; i++) {
		if (i >= times.length) break;

			const t = times[i];
			const temp = Math.round(temps[i]);

			const item = document.createElement('div');
			item.className = 'hour-item';

			const label = document.createElement('div');
			label.className = 'hour-label';
			label.textContent = formatTime(t) || '—';

			const value = document.createElement('div');
			value.className = 'hour-temp';
			value.textContent = `${temp}°`;

		item.appendChild(label);
		item.appendChild(value);
		container.appendChild(item);
	}
}

renderNextHours(5);
