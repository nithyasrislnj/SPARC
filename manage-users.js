let allUsers = [];
let filteredUsers = [];
let masterUsers = [];

let currentRole = "";
let currentPage = 1;

const USERS_PER_PAGE = 10;

/* LOAD USER COUNTS */
async function loadUserCounts() {
    try {
        const response = await fetch(
            `${API_BASE_URL}/api/admin/user-counts`
        );

        const counts = await response.json();

        const volunteer = counts.Volunteer || 0;
        const ngo = counts.NGO || 0;
        const donor = counts.Donor || 0;
        const employer = counts.Employer || 0;

        document.getElementById("volunteerCount").innerText = volunteer;
        document.getElementById("ngoCount").innerText = ngo;
        document.getElementById("donorCount").innerText = donor;
        document.getElementById("employerCount").innerText = employer;

        document.getElementById("totalUsers").innerText =
            volunteer + ngo + donor + employer;
        
    }
    catch (error) {
        console.error(error);
        alert("Unable to load user counts.");
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
        const response = await fetch(
            `${API_BASE_URL}/api/admin/users/${role}`
        );

        const users = await response.json();

        allUsers = users;
        filteredUsers = [...users];
        renderUsers();
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
                    <span class="status-badge">
                        ${user.status}
                    </span>
                </td>
                <td>
                    ${new Date(user.join_date)
                        .toLocaleDateString()}
                </td>
                <td>
                    <button
                        class="delete-btn"
                        onclick="deleteUser(${user.id})">

                        Delete

                    </button>
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
                allUsers=[...masterUsers];
                filteredUsers=[...masterUsers];
                renderUsers();
            }
        }

        else{
            loadUsersByRole(currentRole);
        }
        return;
    }

    if(masterUsers.length===0){
        const response=
            await fetch(
                `${API_BASE_URL}/api/admin/users`
            );

        masterUsers= await response.json();
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


/* DELETE USER */
async function deleteUser(userId) {
    const confirmDelete =
        confirm(
            "Are you sure you want to delete this user?"
        );

    if (!confirmDelete)
        return;

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/api/admin/users/${userId}`,
                {
                    method: "DELETE"
                }
            );

        const result = await response.json();

        if (result.success) {
            alert("User deleted successfully.");
            await loadUserCounts();
            if (currentRole === "All") {
                await loadAllUsers();
            } 
            else {
                await loadUsersByRole(currentRole);
            }
        }

        else {
            alert(result.message);
        }
    }

    catch (error) {
        console.error(error);
        alert("Unable to delete user.");
    }
}

/* PAGE LOAD */
window.onload = async function () {
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
        const response = await fetch(
            `${API_BASE_URL}/api/admin/users`
        );

        const users= await response.json();

        masterUsers=users;

        allUsers=users;
        filteredUsers = [...users];
        renderUsers();
    }

    catch(error){
        console.error(error);
        alert("Unable to load users.");
    }
}