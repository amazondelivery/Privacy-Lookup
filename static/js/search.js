function searchGuide() {
    const input = document.getElementById('search-input');
    const domain = input.value.trim();
    if (domain) {
        window.location.href = `/guides/${domain}`;
    }
}

let error = 0;

document.getElementById("thebutton").addEventListener('click', async () => {
    const domain = document.getElementById('search-input').value;
    const response = await fetch(`/api/guides/${encodeURIComponent(domain)}`);
    const data = await response.json();
    
    if (data.exists) {
        window.location.href = `/guides/${encodeURIComponent(domain)}`;
    } else {
        document.getElementById('results').innerHTML = `No guide found for this website. error no ${error}`;
        error++;
    }
});