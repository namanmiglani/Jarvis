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
const weatherData = {
	hourly: {
		time: hourly.time.map(t => new Date((t + utcOffsetSeconds) * 1000)),
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
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Update current weather (first hour)
const currentTemp = weatherData.hourly.temperature_2m[0];
const currentPrecipProb = weatherData.hourly.precipitation_probability[0];
const currentWind = weatherData.hourly.wind_speed_10m[0];
document.getElementById('temp').textContent = `${Math.round(currentTemp)}°C`;
document.getElementById('precip').textContent = `${Math.round(currentPrecipProb)}% chance of rain`;
document.getElementById('wind').textContent = `${Math.round(currentWind)} km/h wind`;
