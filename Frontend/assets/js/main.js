var 
    // Variables
    profile_name = document.querySelector("#username-container"),
    caret_down = document.querySelector("#caret-down")
    profile_dropdown = document.querySelector(".profile-dropdown");

// Event Listeners
profile_name.addEventListener("click", function () {
    if (profile_dropdown.style.display === "none") {
        profile_dropdown.style.display = "block";
    } else {
        profile_dropdown.style.display = "none";
    }
});

caret_down.addEventListener("click", function() {
    if (profile_dropdown.style.display === "none") {
        profile_dropdown.style.display = "block";
    } else {
        profile_dropdown.style.display = "none";
    }
});