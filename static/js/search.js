function searchGuide() {
    const input = document.getElementById('search-input');
    const domain = input.value.trim();
    
    if (domain) {
        window.location.href = `/guide/${domain}`;
    }
}