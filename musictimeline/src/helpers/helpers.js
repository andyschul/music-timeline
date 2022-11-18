
export function formatDate(dateString) {
    const date = dateString.split('-');
    const month = parseInt(date[1]) - 1;
    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    return `${monthNames[month]} ${parseInt(date[2])}, ${date[0]}`;
}

export function formatArtists(artists) {
    return artists.map(a => a['name']).join(', ');
}