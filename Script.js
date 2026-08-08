let otpCountdown;
let timeLeft = 60;

/* BEAUTIFUL ALERT POPUP */
function showAlert(title, message, type = "success") {
    const modal = document.getElementById("alertModal");
    const icon = document.getElementById("alertIcon");
    const heading = document.getElementById("alertTitle");
    const text = document.getElementById("alertMessage");

    heading.innerHTML = title;
    text.innerHTML = message;

    if (type === "success") {
        icon.innerHTML = "✓";
        icon.style.background = "#16a34a";
    }
    else if (type === "error") {
        icon.innerHTML = "✕";
        icon.style.background = "#dc2626";
    }
    else {
        icon.innerHTML = "!";
        icon.style.background = "#f59e0b";
    }

    modal.style.display = "flex";
}

function closeAlert(){
    document.getElementById("alertModal").style.display = "none";
}


function showLoading(){

    document.getElementById("loadingModal").style.display="flex";

}

function hideLoading(){
    document.getElementById("loadingModal").style.display = "none";
}


function startOtpTimer(){
    clearInterval(otpCountdown);

    timeLeft = 60;

    document.getElementById("otpStatus").innerHTML =
    "📨 OTP sent successfully";

    document.getElementById("resendOtpBtn").style.display = "none";

    document.getElementById("countdownText").style.display = "inline";

    updateCountdown();

    otpCountdown = setInterval(()=>{

        timeLeft--;

        updateCountdown();

        if(timeLeft <= 0){
            clearInterval(otpCountdown);

            document.getElementById("countdownText").style.display="none";

            document.getElementById("otpStatus").innerHTML =
            "Didn't receive the OTP?";

            document.getElementById("resendOtpBtn").style.display="inline-block";
        }
    },1000);
}

function updateCountdown(){
    const minutes =
    String(Math.floor(timeLeft/60)).padStart(2,"0");

    const seconds =
    String(timeLeft%60).padStart(2,"0");

    document.getElementById("countdownText").innerHTML =
    `Resend OTP in ${minutes}:${seconds}`;
}


async function resendOTP(){
    const email =
    document.getElementById("forgotEmail").value.trim();

    const btn =
    document.getElementById("resendOtpBtn");

    btn.disabled = true;
    btn.innerHTML = "Sending...";

    showLoading(
        "Sending OTP...",
        "Please wait while we send a new OTP to your registered email."
    );

    try{
        const response = await fetch(
            `${API_BASE_URL}/forgot_password`,
            {
                method:"POST",
                headers:{
                    "Content-Type":"application/json"
                },
                body:JSON.stringify({
                    email:email
                })
            }
        );

        hideLoading();

        const data = await response.json();

        btn.disabled = false;
        btn.innerHTML = "Resend OTP";

        if(response.ok){
            showAlert(
                "OTP Sent",
                "A new OTP has been sent to your email.",
                "success"
            );

            document.getElementById("forgotOTP").value = "";
            document.getElementById("forgotOTP").focus();

            document.getElementById("otpStatus").innerHTML =
            "📨 New OTP sent successfully";

            startOtpTimer();
        }

        else{
            showAlert(
                "Failed",
                data.message,
                "error"
            );
        }
    }
    catch(error){
        hideLoading();

        btn.disabled = false;
        btn.innerHTML = "Resend OTP";

        showAlert(
            "Connection Error",
            "Unable to resend OTP. Please try again.",
            "error"
        );
    }
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
    if(window.location.pathname.includes("login.html"))
        return;

    document.getElementById("registerModal").style.display="none";
}

/* LOGIN */
function openLogin(){
  document.getElementById("loginModal").style.display="flex";
}

function closeLogin(){
    if(window.location.pathname.includes("login.html"))
        return;

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

  const rememberMe =
  document.getElementById("rememberMe").checked;

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

    showAlert(
      "Login Successful",
      "Welcome back to SPARC!"
    );
    

    document.getElementById(
      "message"
    ).innerHTML = "Login Successful";

    closeLogin();

    /* Save complete logged-in user */
    localStorage.setItem("loggedInUser", JSON.stringify({
      token: data.token,
      name: data.name,
      email: data.email,
      role: data.role,
      darkMode: data.darkMode
    }));

    if(rememberMe){
      localStorage.setItem(
        "rememberMe",
        "true"
      );
    }

    else{
      localStorage.removeItem(
        "rememberMe"
      );
    }

    /* Redirect to Home Page */
    window.location.href = "home.html";
    
  }

  else{
    showAlert(
        "Login Failed",
        data.message,
        "error"
    );
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

  if(response.ok){
    showAlert(
        "Registration Successful",
        data.message,
        "success"
    );
  }
  else{
    showAlert(
        "Registration Failed",
        data.message,
        "error"
    );
  }
  
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


/* Dashboard Click 
function openDashboard(){

    const token = localStorage.getItem("token");
    const role = localStorage.getItem("role");

    if(!token || !role){
        alert("Please Login First");
        openLogin();
        return;
    }

     OPEN USER'S OWN DASHBOARD 
    localStorage.setItem(
        "activeRole",
        role
    );

    window.location.href = "dashboard.html";
} 
*/

function openDashboard(){

    if(!localStorage.getItem("token")){

        window.location.href = "login.html";

        return;

    }

    window.location.href = "dashboard.html";

}

function logout(){
    localStorage.removeItem("token");
    localStorage.removeItem("loggedInUser");
    localStorage.removeItem("rememberMe");
    localStorage.removeItem("name");
    localStorage.removeItem("email");
    localStorage.removeItem("role");
    localStorage.removeItem("darkMode");
    localStorage.removeItem("activeRole");

    window.location.href = "login.html";
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

/* Close Profile Menu */
function closeProfileMenu() {
    document.getElementById("profileMenu").style.display = "none";
    document.getElementById("mainContent").classList.remove("blur-bg");
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
    closeProfileMenu();
    document.getElementById("sidePanel").classList.add("active");
    document.body.style.overflow = "hidden";
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
    closeProfileMenu();
    document.getElementById("sidePanel").classList.add("active");
    document.body.style.overflow = "hidden";
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

    closeProfileMenu();
    document.getElementById("sidePanel").classList.add("active");
    document.body.style.overflow = "hidden";
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

    document.getElementById("mainContent").classList.remove("blur-bg");
    document.body.style.overflow = "";
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


/* MOBILE NAVIGATION */
function toggleMenu(){
    const navbar = document.getElementById("navbar");
    if(navbar){
      navbar.classList.toggle("show");
    }
}
 

/* Close menu after clicking a link */
document.addEventListener("DOMContentLoaded", () => {
    const links =
    document.querySelectorAll("#navbar a");

    links.forEach(link => {
        link.addEventListener("click", () => {
            document
                .getElementById("navbar")
                .classList.remove("show");
        });
    });
});


/* LOGIN BUTTON / PROFILE BUTTON */
window.addEventListener("DOMContentLoaded", () => {
    const loginBtn = document.getElementById("loginBtn");
    const profileBtn = document.getElementById("profileBtn");

    if(!loginBtn || !profileBtn)
        return;

    const token = localStorage.getItem("token");
    const name = localStorage.getItem("name");

    if(token && name){
        // Hide Login button
        loginBtn.style.display = "none";

        // Show logged-in person's name
        profileBtn.style.display = "inline-block";

        profileBtn.innerHTML =
        "👤 " + localStorage.getItem("name");
    }

    else{
        // Show Login button
        loginBtn.style.display = "inline-block";
        // Hide Profile/Name button
        profileBtn.style.display = "none";
    }
});


/* FORGOT PASSWORD */
function openForgotPassword(){
    document.getElementById("forgotPasswordModal").style.display="flex";
}

function closeForgotPassword(){
    clearInterval(otpCountdown);

    document.getElementById("forgotPasswordModal").style.display="none";

    document.getElementById("forgotStep1").style.display="block";
    document.getElementById("forgotStep2").style.display="none";
    document.getElementById("forgotStep3").style.display="none";

    document.getElementById("forgotEmail").value="";
    document.getElementById("forgotOTP").value="";
    document.getElementById("forgotNewPassword").value="";
    document.getElementById("forgotConfirmPassword").value="";

    timeLeft = 60;

    document.getElementById("countdownText").style.display="inline";
    document.getElementById("countdownText").innerHTML =
    "Resend OTP in 01:00";

    document.getElementById("otpStatus").innerHTML =
    "📨 OTP sent successfully";

    document.getElementById("resendOtpBtn").style.display="none";
}


async function sendOTP(){
    const email = document.getElementById("forgotEmail").value.trim();

    if(email === ""){
        showAlert(
            "Missing Email",
            "Please enter your registered email.",
            "error"
        );
        return;
    }

    // Get Send OTP button
    const btn = document.getElementById("sendOtpBtn");

    btn.disabled = true;
    btn.innerHTML = "Sending OTP...";
    btn.style.opacity = "0.7";
    btn.style.cursor = "not-allowed";

    showLoading();

    try{
        const response = await fetch(
            `${API_BASE_URL}/forgot_password`,
            {
                method:"POST",
                headers:{
                    "Content-Type":"application/json"
                },
                body:JSON.stringify({
                    email:email
                })
            }
        );

        hideLoading();

        btn.disabled = false;
        btn.innerHTML = "Send OTP";
        btn.style.opacity = "1";
        btn.style.cursor = "pointer";

        const data = await response.json();

        if(response.ok){
            showAlert(
                "OTP Sent",
                "A 6-digit OTP has been sent to your email.",
                "success"
            );

            document.getElementById("forgotStep1").style.display = "none";
            document.getElementById("forgotStep2").style.display = "block";

            document.getElementById("otpStatus").innerHTML =
            "📨 OTP sent successfully";

            startOtpTimer();

            document.getElementById("forgotOTP").focus();
        }

        else{
            showAlert(
                "Failed",
                data.message,
                "error"
            );
        }
    }

    catch(error){
        hideLoading();

        btn.disabled = false;
        btn.innerHTML = "Send OTP";
        btn.style.opacity = "1";
        btn.style.cursor = "pointer";

        showAlert(
            "Connection Error",
            "Unable to contact the server. Please try again.",
            "error"
        );
    }
}

async function verifyOTP(){
    const email =
    document.getElementById("forgotEmail").value;

    const otp =
    document.getElementById("forgotOTP").value.trim();

    if(otp.length !== 6){
      showAlert(
        "Invalid OTP",
        "Please enter the 6-digit OTP.",
        "error"
      );
      return;
    }

    if(otp===""){
        showAlert(
            "Missing OTP",
            "Please enter the OTP.",
            "error"
        );
        return;
    }

    const response =
    await fetch(
        `${API_BASE_URL}/verify_otp`,
        {
            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify({
                email,
                otp
            })
        }
    );

    const data =
    await response.json();

    if(response.ok){
        showAlert(
            "OTP Verified",
            data.message,
            "success"
        );

        document.getElementById("forgotStep2").style.display="none";
        document.getElementById("forgotStep3").style.display="block";
        document.getElementById("forgotNewPassword").focus();
    }

    else{
        showAlert(
            "Verification Failed",
            data.message,
            "error"
        );
    }
}


async function resetPassword(){
    const email =
    document.getElementById("forgotEmail").value;

    const password =
    document.getElementById("forgotNewPassword").value;

    const confirm =
    document.getElementById("forgotConfirmPassword").value;

    if(password !== confirm){
        showAlert(
            "Password Mismatch",
            "Both passwords must match.",
            "error"
        );

        return;
    }

    const response =
    await fetch(
        `${API_BASE_URL}/reset_password`,
        {
            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify({
                email,
                password
            })
        }
    );

    const data =
    await response.json();

    if(response.ok){
        showAlert(
            "Password Updated",
            "Your password has been reset successfully.",
            "success"
        );

        closeForgotPassword();

        openLogin();

        document.getElementById("forgotStep1").style.display="block";
        document.getElementById("forgotStep2").style.display="none";
        document.getElementById("forgotStep3").style.display="none";

        document.getElementById("forgotEmail").value="";
        document.getElementById("forgotOTP").value="";
        document.getElementById("forgotNewPassword").value="";
        document.getElementById("forgotConfirmPassword").value="";

    }

    else{
        showAlert(
            "Reset Failed",
            data.message,
            "error"
        );
    }
}


/* Auto-fill Email and Role*/
window.addEventListener("DOMContentLoaded",()=>{
    if(localStorage.getItem("rememberMe")==="true"){

        const email =
        localStorage.getItem("email");

        const role =
        localStorage.getItem("role");

        if(email){
            document.getElementById("email").value =
            email;
        }

        if(role){
            document.getElementById("role").value =
            role;
        }

        const remember =
        document.getElementById("rememberMe");

        if(remember){
            remember.checked = true;
        }
    }
});