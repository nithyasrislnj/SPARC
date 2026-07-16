/* Join Volunteer */
function joinVolunteer(){
    openRegister(true);
}

/* EXPLORE PLATFORM */
function explorePlatform(){
    window.location.href = "how-sparc-works.html";
}


/* REGISTER */
function openRegister(fromVolunteer = false){
    document.getElementById(
        "registerModal"
    ).style.display = "flex";

    const roleDropdown =
    document.getElementById("regRole");

    if(fromVolunteer){
        roleDropdown.value = "Volunteer";

        roleDropdown.disabled = true;
    }

    else{
        roleDropdown.disabled = false;

        roleDropdown.selectedIndex = 0;

        localStorage.removeItem("selectedRole");
    }
}

function closeRegister(){
  document.getElementById(
    "registerModal"
  ).style.display="none";
}


/* LOGIN */
function openLogin(){
  document.getElementById("loginModal").style.display="flex";
}

function closeLogin(){
  document.getElementById("loginModal").style.display="none";
}

document
.getElementById("loginForm")
.addEventListener("submit", async(e)=>{

  e.preventDefault();

  const email =
  document.getElementById("email").value;

  const password =
  document.getElementById("password").value;

  const role =
  document.getElementById("role").value;

  const response =
  await fetch(
    `${API_BASE_URL}/login` ,
    {
      method:"POST",
      headers:{
        "Content-Type":"application/json"
      },
      body:JSON.stringify({
        email,
        password,
        role
      })
    }
  );

  const data =
  await response.json();

  if(response.ok){

    localStorage.setItem(
      "token",
      data.token
    );

    localStorage.setItem(
      "name",
      data.name
    );

    localStorage.setItem(
      "role",
      data.role
    );

    /* REMOVE PREVIOUS DASHBOARD SELECTION */
    localStorage.removeItem("activeRole");

    localStorage.setItem(
      "email",
      data.email
    );

    localStorage.setItem(
      "darkMode",
      data.darkMode
    );

    document.getElementById(
      "message"
    ).innerHTML=
    "Login Successful";
    

    document.getElementById(
      "message"
    ).innerHTML = "Login Successful";

    closeLogin();

    if(document.querySelector(".role-card")){
      highlightRole(data.role);
    }
    
  }
  else{
    document.getElementById(
      "message"
    ).innerHTML=
    data.message;
  }
  
});

/* Registration Logic */
document
.getElementById("registerForm")
.addEventListener("submit", async(e)=>{

  e.preventDefault();

  const name =
  document.getElementById(
    "regName"
  ).value;

  const email =
  document.getElementById(
    "regEmail"
  ).value;

  const password =
  document.getElementById(
    "regPassword"
  ).value;

  const role =
  document.getElementById(
    "regRole"
  ).value;

  const response =
  await fetch(
    `${API_BASE_URL}/register` ,
    {
      method:"POST",
      headers:{
        "Content-Type":"application/json"
      },
      body:JSON.stringify({
        name,
        email,
        password,
        role
      })
    }
  );

  const data =
  await response.json();

  document.getElementById(
    "registerMessage"
  ).innerHTML =
  data.message;
  
  if(response.ok){
    setTimeout(()=>{
      closeRegister();

      const role = localStorage.getItem("selectedRole");

      openLogin();

      if(role){
        document.getElementById("role").value = role;

        document.getElementById("role").disabled = true;
      }
    },1500);
  }

});


/* Logged-in Role */
window.addEventListener("load",()=>{
  const darkMode = localStorage.getItem("darkMode");

  if(darkMode === "true"){
    document.body.classList.add("dark-theme");
  }
});


/* Dashboard Click */
function openDashboard(){

    const token = localStorage.getItem("token");
    const role = localStorage.getItem("role");

    if(!token || !role){
        alert("Please Login First");
        openLogin();
        return;
    }

    /* OPEN USER'S OWN DASHBOARD */
    localStorage.setItem(
        "activeRole",
        role
    );

    window.location.href = "dashboard.html";
}


/* Logout */
function logout(){
    localStorage.clear();

    document.body.style.background="#fff";

    document.body.style.color="#000";

    document
    .getElementById("mainContent")
    .classList.remove("blur-bg");

    location.reload();
}


/* Profile Menu */
async function toggleProfileMenu(){
    if( !localStorage.getItem("token") )
      {
        alert(
          "Please Login First"
        );
        return;
    }

    const menu =
    document.getElementById(
        "profileMenu"
    );

    if(menu.style.display==="block"){

        menu.style.display="none";

        document
        .getElementById("mainContent")
        .classList.remove("blur-bg");

        return;
    }

    const email=localStorage.getItem("email");

    const response=await fetch(
        `${API_BASE_URL}/profile/${email}`
    );

    const user=await response.json();

    document.getElementById(
        "profileName"
    ).innerHTML =
    "👤 " +
    (localStorage.getItem("name") || "");

    document.getElementById(
        "profileRole"
    ).innerHTML =
    "🏷 " +
    (localStorage.getItem("role") || "");

    document.getElementById(
        "profileEmail"
    ).innerHTML =
    "📧 " +
    (localStorage.getItem("email") || "");

    document.getElementById(
        "profileStatus"
    ).innerHTML =
    "🟢 " 
    +user.status
    + "<br>📅 Member Since: "
    + new Date(user.join_date).toLocaleDateString();

    menu.style.display = "block";

    document
    .getElementById("mainContent")
    .classList.add("blur-bg");

    window.scrollTo({
      top: window.scrollY
    });
}


async function openNotifications(){
    const email = localStorage.getItem("email");

    const response = await fetch(
        `${API_BASE_URL}/get_notifications/${email}`
    );

    const data = await response.json();

    document.getElementById("panelTitle").innerHTML = "🔔 Notifications";

    let html = "";

    if(data.length === 0){
        html = "<p>No Notifications</p>";
    }
    else{
        data.forEach(item=>{
            html += `
            <div class="panel-item">
                <b>🔔 ${item.title}</b>
                <br>
                <small>${new Date(item.time).toLocaleString()}</small>
                <hr>
            </div>
            `;
        });
    }
    document.getElementById("panelContent").innerHTML = html;
    document.getElementById("sidePanel").classList.add("active");
    document.getElementById("mainContent").classList.add("blur-bg");
}

function closeNotif(){
  document.getElementById("notifModal").style.display="none";
  document.getElementById("mainContent").classList.remove("blur-bg");
}



async function openActivity(){
    const email = localStorage.getItem("email");
    const response = await fetch(
        `${API_BASE_URL}/get_activity/${email}`
    );

    const data = await response.json();

    document.getElementById("panelTitle").innerHTML = "📈 Activity";

    let html = "";

    if(data.length === 0){
        html = "<p>No Activity</p>";
    }
    else{
        data.forEach(item=>{
            html += `
            <div class="panel-item">
                <b>📋 ${item.description}</b>
                <br>
                <small>${new Date(item.time).toLocaleString()}</small>
                <hr>
            </div>
            `;
        });
    }
    document.getElementById("panelContent").innerHTML = html;
    document.getElementById("sidePanel").classList.add("active");
    document.getElementById("mainContent").classList.add("blur-bg");
}


function closeActivity(){
  document.getElementById("activityModal").style.display="none";
  document.getElementById("mainContent").classList.remove("blur-bg");
}




function openSettings(){

  const email = localStorage.getItem("email");

  fetch(`${API_BASE_URL}/profile/${email}`)
  .then(res => res.json())
  .then(data => {

    document.getElementById("panelTitle").innerText = "⚙ Settings";

    document.getElementById("panelContent").innerHTML = `
      <p>Name: ${data.name}</p>
      <p>Email: ${data.email}</p>
      <p>Role: ${data.role}</p>
      <button onclick="showChangePassword()">Change Password</button>
      <button onclick="toggleDarkMode()">Dark Mode</button>
    `;

    document.getElementById("sidePanel").classList.add("active");

    document.getElementById("mainContent").classList.add("blur-bg");

  });
}


function showEditProfile(){
document.getElementById(
"editProfileModal"
).style.display="flex";

document.getElementById(
"editName"
).value=
localStorage.getItem("name");

document.getElementById(
"editEmail"
).value=
localStorage.getItem("email");

}



function closeEditProfile(){
document.getElementById(
"editProfileModal"
).style.display="none";

}


async function saveProfile(){
const name=
document.getElementById(
"editName"
).value;

const email=
document.getElementById(
"editEmail"
).value;

const oldEmail=
localStorage.getItem(
"email"
);

const response=
await fetch(
`${API_BASE_URL}/edit_profile` ,
{

method:"POST",

headers:{
"Content-Type":
"application/json"
},

body:JSON.stringify({

old_email:oldEmail,

name:name,

email:email

})

});

const data=
await response.json();

alert(data.message);

localStorage.setItem("name", name);

localStorage.setItem("email", email);

document.getElementById("profileName").innerHTML =
"👤 " + name;

document.getElementById("profileEmail").innerHTML =
"📧 " + email;

closeEditProfile();

toggleProfileMenu();

}


function showChangePassword(){
  document.getElementById("panelContent").innerHTML = `
    <input type="password" id="oldPass" placeholder="Old Password">

    <br><br>

    <input type="password" id="newPass" placeholder="New Password">
    <button onclick="updatePassword()">Update</button>
  `;
}


function updatePassword(){
  const email = localStorage.getItem("email");

  fetch(`${API_BASE_URL}/change-password`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      email,
      oldPassword: document.getElementById("oldPass").value,
      newPassword: document.getElementById("newPass").value
    })
  })
  .then(res => res.json())
  .then(data => {
    alert(data.message);
  });

}

function toggleDarkMode(){
  const email = localStorage.getItem("email");

  fetch(`${API_BASE_URL}/toggle-darkmode`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ email:email })
  })
  .then(res => res.json())
  .then(data => {

    if(data.darkMode){
      document.body.classList.add("dark-theme");

      localStorage.setItem("darkMode",true);
      /* document.body.style.background="#111";
      document.body.style.color="#fff"; */
    }

    else{
      document.body.classList.remove("dark-theme");

      localStorage.setItem("darkMode",false);

      /* document.body.style.background="#fff";
      document.body.style.color="#000"; */
    }

  });
}


function closeSettings(){
  document.getElementById("settingsModal").style.display="none";
  document.getElementById("mainContent").classList.remove("blur-bg");
}

function closePanel(){
    document
    .getElementById("sidePanel")
    .classList.remove("active");
}

/* Dashboard Greetings 
function getGreeting(){
  const hour = new Date().getHours();

  if(hour < 12){
    return "Good Morning ☀️";
  }

  if(hour < 17){
    return "Good Afternoon 🌤";
  }

  return "Good Evening 🌙";
}

/* Role-based Dashboard Header 
function getRoleInfo(role){
  switch(role){
    case "Volunteer":
      return{
          badge:"🤝 Active Volunteer",
          message:"Together we can make every meal count."
      };

      case "Donor":
        return{
          badge:"🍱 Active Donor",
          message:"Thank you for helping reduce food waste."
        };

      case "NGO":
        return{
          badge:"🏢 Active NGO",
          message:"Serving communities with care."
      };

      case "Employer":
        return{
          badge:"💼 Active Employer",
          message:"Creating opportunities for a better future."
      };

      case "Admin":
        return{
          badge:"👑 System Administrator",
          message:"Keeping SPARC running smoothly."
        };

      default:
        return{
          badge:"🟢 Active Member",
          message:"Welcome to SPARC."
        };
  }
}

function toggleStatistics(){
    const chart =
    document.getElementById("chartContainer");

    const button =
    document.getElementById("chartToggleBtn");

    if(chart.style.display === "none"){
        chart.style.display = "block";

        button.innerHTML ="📉 Hide Statistics";
    }
    else{
        chart.style.display = "none";
        button.innerHTML ="📈 Show Statistics";
    }
} */

function toggleMenu(){
    document
        .getElementById("mobileNav")
        .classList.toggle("show-menu");
}

/* ==========================
   MOBILE NAVIGATION
========================== */

function toggleMenu(){
    const nav =
    document.getElementById("navbar");

    nav.classList.toggle("show");
}


/* Close menu after clicking a link */
document.addEventListener("DOMContentLoaded", () => {
    const links =
    document.querySelectorAll("#navMenu a");

    links.forEach(link => {
        link.addEventListener("click", () => {

            document
                .getElementById("navMenu")
                .classList.remove("show");
        });
    });
});