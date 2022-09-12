document.addEventListener('DOMContentLoaded', function() {
    node = document.getElementById('search-bar')
    node.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            }
        })
    })

document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('click', function(e){
        console.log(e.target.id);
        if (e.target.id === 'card-results' || e.target.type === 'search') {
            return false
        }
        box = document.getElementById('search-results')
        box.style.display="none"
    })
})
