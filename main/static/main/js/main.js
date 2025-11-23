const $ = (id) => document.getElementById(id);

function showError(message){
    const el = $('error');
    el.hidden = false;
    el.textContent = message;
    $(result).hidden = true;
}

function hideError(){
    $('error').hidden = true;
}

async function fetchWeather(city,country){
    const url = `/api/weather?city=${encodeURIComponent(city)}&country=${encodeURIComponent(country)}`;
    const res = await fetch(url,{ method: 'GET' , headers: { "X-Requested-With": "fetch" } });
    if (!res.ok) { throw new Error(`HTTP error! status: ${res.status}`);  }
    return await res.json();
}

function renderWeather(data){
    hideError();
    $('result').hidden = false;
    $('cityTitle').textContent = `${data.city}, ${data.country}`;
    $('temp').textContent = data.current.temp;
    $('summary').textContent = data.current.summary;
    const updatedDate = new Date(data.current.dt * 1000);
    $('updated').textContent = `Updated at: ${updatedDate.toLocaleString()}`;
    // Additional rendering logic for forecastChart can be added here
}

function debounce(fn, wait = 400) {
  let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), wait); };
}


$('search-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const city = $('id_city').value.trim();
    const country = $('id_country').value.trim() || "MX"; 
    if (!city || !country) {
        showError('Please enter both city and country.');
        return;
    }
    try {
        const weatherData = await fetchWeather(city, country);
        renderWeather(weatherData);
    } catch (error) {
        console.error('Error fetching weather data:', error);
        showError("City not found or API error.");
    }
});

/*
$("id_city").addEventListener("input", debounce(async () => {
  const city = $("id_city").value.trim();
  if (city.length < 3) return;
}, 300));*/