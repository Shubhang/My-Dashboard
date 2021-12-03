/* Set the width of the sidebar to 250px and the left margin of the page content to 250px */
function openNav() {
    document.getElementById("mySidebar").style.width = "250px";
    document.getElementById("main").style.marginLeft = "250px";
}

/* Set the width of the sidebar to 0 and the left margin of the page content to 0 */
function closeNav() {
    document.getElementById("mySidebar").style.width = "0";
    document.getElementById("main").style.marginLeft = "0";
}

function toStocks() {
    document.getElementById("stocks").style.display = "block";
    document.getElementById("summaries").style.display = "none";
    document.getElementById("sentiment").style.display = "none";
}

function toSummaries() {
    document.getElementById("stocks").style.display = "none";
    document.getElementById("summaries").style.display = "block";
    document.getElementById("sentiment").style.display = "none";
}

function toSentiment() {
    document.getElementById("stocks").style.display = "none";
    document.getElementById("summaries").style.display = "none";
    document.getElementById("sentiment").style.display = "block";
}

// handles users that use the keyboard
function handleFirstTab(e) {
    if (e.keyCode === 9) { // the "I am a keyboard user" key
        document.body.classList.add('user-is-tabbing');
        window.removeEventListener('keydown', handleFirstTab);
    }
}

window.addEventListener('keydown', handleFirstTab);