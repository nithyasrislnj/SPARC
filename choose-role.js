/* SELECT ROLE */

function selectRole(role){

    const loginRole = localStorage.getItem("role");

    if(!loginRole){
        alert("Please Login First");
        openLogin();
        return;
    }

    /* ADMIN CAN ACCESS ALL DASHBOARDS */
    if(loginRole === "Admin"){
        localStorage.setItem("activeRole", role);

        localStorage.setItem(
            "dashboardPreviouspage",window.location.href
        );

        window.location.href = "dashboard.html";
        return;
    }

    /* OTHER USERS CAN ACCESS ONLY THEIR ROLE */
    if(role !== loginRole){
        alert(
            "Access Denied.\nYou logged in as " + loginRole
        );
        return;
    }

    localStorage.setItem("activeRole", role);

    localStorage.setItem(
        "dashboardPreviouspage",window.location.href
    );

    window.location.href = "dashboard.html";
}

/* Highlight Logged-in Role */
function highlightRole(role){
    const dark = document.body.classList.contains("dark-theme");

    document
    .querySelectorAll(".role-card")
    .forEach(card=>{

        card.style.border =
        "1px solid var(--border)";

        card.style.background =
        dark ? "var(--card)" : "#ffffff";

        const title =
        card.querySelector("h3").innerText;

        if(title === role){
            card.style.border =
            "3px solid #0f7a2f";

            card.style.background =
            dark ? "#1f3a2e" : "#f0fdf4";
        }
    });
}

/* LOAD CHOOSE ROLE PAGE */
window.addEventListener("load", ()=>{

    const role =
    localStorage.getItem("role");

    if(role){

        highlightRole(role);

    }

});