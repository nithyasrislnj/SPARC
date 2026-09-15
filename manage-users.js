let allUsers = [];
let filteredUsers = [];
let masterUsers = [];

let currentRole = "";
let currentPage = 1;
let currentStatus = "";

const USERS_PER_PAGE = 10;


function animateCount(elementId, targetValue, duration = 1200) {
    const element =
        document.getElementById(elementId);

    const startTime =
        performance.now();

    function updateCount(currentTime) {
        const elapsed =
            currentTime - startTime;

        const progress =
            Math.min(elapsed / duration, 1);

        // Smooth animation
        const easedProgress =
            1 - Math.pow(1 - progress, 3);

        const currentValue =
            Math.floor(targetValue * easedProgress);

        element.innerText =
            currentValue;

        if(progress < 1){
            requestAnimationFrame(
                updateCount
            );
        }
        else{
            element.innerText =
                targetValue;
        }
    }

    requestAnimationFrame(
        updateCount
    );
}


/* LOAD USER COUNTS */
async function loadUserCounts() {
    try {
        const adminEmail =
            localStorage.getItem("email");

        const response =
            await fetch(
                `${API_BASE_URL}/api/admin/user-counts?email=${encodeURIComponent(adminEmail)}`
            );

        if(!response.ok){
            throw new Error(
                "Unable to load user counts"
            );
        }

        const counts =
            await response.json();

        const volunteer =
            counts.Volunteer || 0;

        const ngo =
            counts.NGO || 0;

        const donor =
            counts.Donor || 0;

        const employer =
            counts.Employer || 0;

        animateCount(
            "volunteerCount",
            volunteer
        );

        animateCount(
            "ngoCount",
            ngo
        );

        animateCount(
            "donorCount",
            donor
        );

        animateCount(
            "employerCount",
            employer
        );

        animateCount(
            "totalUsers",
            counts.Total || 0
        );
    }

    catch(error){
        console.error(
            "User count error:",
            error
        );
    }
}

/* LOAD USERS BY ROLE */
async function loadUsersByRole(role) {
    currentRole = role;
    currentPage = 1;
    highlightCard(role);

    const container =
        document.getElementById("usersTableContainer");

    container.innerHTML = `
        <div class="dashboard-actions">
            <p style="text-align:center">
                Loading ${role}s...
            </p>
        </div>
    `;

    try {
        const adminEmail =
            localStorage.getItem("email");

        const response =
            await fetch(
                `${API_BASE_URL}/api/admin/users/${role}?email=${encodeURIComponent(adminEmail)}`
            );

        if(!response.ok){
            throw new Error(
                "Unable to load users"
            );
        }

        const users =
            await response.json();

        allUsers = users;

        if(currentStatus===""){
            filteredUsers=[...allUsers];
            renderUsers();
        }
        else{
            filterByStatus(currentStatus);
        }
    }

    catch (error) {
        console.error(error);

        container.innerHTML = `
            <div class="dashboard-actions">
                <p style="color:red;text-align:center">
                    Failed to load users.
                </p>
            </div>
        `;
    }
}

function highlightCard(role){
    document
        .querySelectorAll(".clickable-card")
        .forEach(card=>{

            card.classList.remove("active");
            if(card.dataset.role===role){
                card.classList.add("active");
            }
        });
}

/* RENDER USERS */
function renderUsers() {
    const container =
        document.getElementById("usersTableContainer");

    if (filteredUsers.length === 0) {
        container.innerHTML = `
            <div class="dashboard-actions">
                <h3>No Users Found</h3>
            </div>
        `;
        document.getElementById("pagination").innerHTML = "";
        return;
    }

    const start = (currentPage - 1) * USERS_PER_PAGE;

    const end = start + USERS_PER_PAGE;

    const users = filteredUsers.slice(start, end);

    let html = `
        <table class="users-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Joined</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
    `;

    users.forEach(user => {
        html += `
            <tr>
                <td>${user.name}</td>
                <td>${user.email}</td>
                <td>${user.role}</td>
                <td>
                    <span class="status-badge ${user.status === 'Active' ? 'active-status' : 'inactive-status'}">
                        ${user.status}
                    </span>
                </td>
                <td>
                    ${new Date(user.join_date)
                        .toLocaleDateString()}
                </td>
                <td>
                    ${
                        user.status === "Active"
                        ?
                        `
                            <button
                                class="delete-btn"
                                onclick="toggleUserStatus(${user.id})">

                                Deactivate

                            </button>
                        `
                        :
                        `
                            <button
                                class="primary-btn"
                                onclick="toggleUserStatus(${user.id})">

                                Reactivate

                            </button>
                        `
                    }
                </td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    `;

    container.innerHTML = html;
    renderPagination();
}

/* SEARCH USERS */
document
.getElementById("userSearch")
.addEventListener("input",async function(){

    const keyword=this.value.trim().toLowerCase();

    if(keyword===""){
        if(currentRole==="All"){
            if(masterUsers.length===0){
                await loadAllUsers();
            }

            else{
                allUsers = [...masterUsers];
                if(currentStatus===""){
                    filteredUsers=[...allUsers];
                    renderUsers();
                }
                else{
                    filterByStatus(currentStatus);
                }
            }
        }

        else{
            loadUsersByRole(currentRole);
        }
        return;
    }

    if(masterUsers.length===0){
        const adminEmail =
            localStorage.getItem("email");

        const response =
            await fetch(
                `${API_BASE_URL}/api/admin/users?email=${encodeURIComponent(adminEmail)}`
            );

        if(!response.ok){
            throw new Error(
                "Unable to load users"
            );
        }

        masterUsers =
            await response.json();
    }

    filteredUsers=masterUsers.filter(user=>
        user.name.toLowerCase().includes(keyword) ||
        user.email.toLowerCase().includes(keyword)
    );

    currentPage=1;
    renderUsers();

    const roles=
        [...new Set(filteredUsers.map(u=>u.role))];

    if(roles.length===1){
        highlightCard(roles[0]);
    }

    else{
        highlightCard("All");
    }
});

/* PAGINATION */
function renderPagination() {
    const container =
        document.getElementById("pagination");

    const totalPages =
        Math.ceil(filteredUsers.length / USERS_PER_PAGE);

    if (totalPages <= 1) {
        container.innerHTML = "";
        return;
    }

    let html = "";

    html += `
        <button
            class="primary-btn"
            ${currentPage === 1 ? "disabled" : ""}
            onclick="previousPage()">
            ◀ Previous
        </button>
    `;

    html += `
        <span
            style="
                margin:0 20px;
                font-weight:bold;
            ">

            Page ${currentPage} of ${totalPages}
        </span>
    `;

    html += `
        <button
            class="primary-btn"
            ${currentPage === totalPages ? "disabled" : ""}
            onclick="nextPage()">
            Next ▶
        </button>
    `;

    container.innerHTML = html;
}


function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        renderUsers();
    }
}


function nextPage() {
    const totalPages =
        Math.ceil(filteredUsers.length / USERS_PER_PAGE);

    if (currentPage < totalPages) {
        currentPage++;
        renderUsers();
    }
}


/* TOGGLE USER STATUS */
async function toggleUserStatus(userId){

    const confirmAction=confirm(
        "Do you want to change this user's account status?"
    );

    if(!confirmAction)
        return;

    try{
        const adminEmail =
            localStorage.getItem("email");

        const response =
            await fetch(
                `${API_BASE_URL}/api/admin/users/${userId}?email=${encodeURIComponent(adminEmail)}`,
                {
                    method:"PUT"
                }
            );

        const result=await response.json();

        if(result.success){

            alert(
                result.status==="Active"
                ?
                "User reactivated successfully."
                :
                "User deactivated successfully."
            );

            await loadUserCounts();

            if(currentRole==="All"){
                await loadAllUsers();
            }
            else{
                await loadUsersByRole(currentRole);
            }

        }
        else{
            alert(result.message);
        }

    }
    catch(error){
        console.error(error);
        alert("Unable to update user status.");
    }

}

/* PAGE LOAD */
window.onload = async function () {
    if (localStorage.getItem("darkMode") === "true") {
        document.body.classList.add("dark-theme");
    }
    await loadUserCounts();
};


async function loadAllUsers() {
    currentRole = "All";
    currentPage = 1;
    highlightCard("All");

    const container =
        document.getElementById("usersTableContainer");

    container.innerHTML = `
        <div class="dashboard-actions">
            <p style="text-align:center; color:green;">
                Loading users...
            </p>
        </div>
    `;

    try {
        const adminEmail =
            localStorage.getItem("email");

        const response =
            await fetch(
                `${API_BASE_URL}/api/admin/users?email=${encodeURIComponent(adminEmail)}`
            );

        if(!response.ok){
            throw new Error(
                "Unable to load users"
            );
        }

        const users =
            await response.json();

        masterUsers=users;

        allUsers = users;

        if(currentStatus===""){
            filteredUsers=[...allUsers];
            renderUsers();
        }
        else{
            filterByStatus(currentStatus);
        }
    }

    catch(error){
        console.error(error);
        alert("Unable to load users.");
    }
}

function filterByStatus(status){

    currentStatus = status;
    currentPage = 1;

    filteredUsers = allUsers.filter(
        user => user.status === status
    );

    renderUsers();

    document
        .querySelectorAll(".status-filter .primary-btn")
        .forEach(btn => btn.classList.remove("active"));

    if(status==="Active"){
        document.getElementById("activeBtn").classList.add("active");
    }

    if(status==="Inactive"){
        document.getElementById("inactiveBtn").classList.add("active");
    }
}