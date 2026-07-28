let dashboardChart = null;

/* Dashboard Greetings */
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

/* Role-based Dashboard Header */
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
}


/* Load Dashboard */
async function loadDashboard(role){
  try{
      const email = localStorage.getItem("email");
      const response =
      await fetch(
      `${API_BASE_URL}/api/dashboard/${role}/${email}`
      );

      const data = await response.json();

      document.querySelector("#dashboard h2").innerText =
      role + " Dashboard";

      const cards = document.querySelector(".dashboard-grid");

      const greeting = getGreeting();

      const roleInfo = getRoleInfo(role);

      document.getElementById("dashboardStatus").innerText = roleInfo.badge;

      const dashboard = document.getElementById("dashboard");

      const welcome = `
        <div class="dashboard-header">
          <div class="welcome-section">
            <h2>👋 Welcome, ${localStorage.getItem("name")}</h2>
            <p>${greeting}</p>
            <p class="dashboard-message">${roleInfo.message}</p>
            <p class="dashboard-role">${role}</p>
          </div>
        </div>
      `;
      
      const summary = `
        <br>
        <h3 class="dashboard-section-title">Today's Summary</h3>

        <div class="summary-grid">
          <div class="summary-card">
            <h3>🔔</h3>
            <p>Notifications</p>
            <h2 id="summaryNotifications">${data.notifications || 0}</h2>
          </div>

          <div class="summary-card">
            <h3>📋</h3>
            <p>Today's Activity</p>
            <h2 id="summaryActivity">${data.today_activity || 0}</h2>
          </div>

          <div class="summary-card">
            <h3>⏳</h3>
            <p>Pending Tasks</p>
            <h2 id="summaryPending">0</h2>
          </div>

          <div class="summary-card">
            <h3>📈</h3>
            <p>Performance</p>
            <h2 id="summaryPerformance">0%</h2>
          </div>
        </div>
      `;

      dashboard.querySelector(".dashboard-summary").innerHTML = summary;

      document.getElementById("dashboardWelcome").innerHTML = welcome;

      dashboard.querySelector(".dashboard-grid").innerHTML = cards.innerHTML;

      /* NOW update IDs */
      updateDashboardSummary(role, data);


      if(role==="Volunteer"){

        cards.innerHTML = `
        <div class="dashboard-card green-box">
            <p>Applications</p>
            <h3>${data.applications}</h3>
        </div>

        <div class="dashboard-card blue-box">
            <p>Pending Beneficiaries</p>
            <h3>${data.pending_beneficiaries}</h3>
        </div>
        `;
      }

      else if(role==="NGO"){

        cards.innerHTML = `
        <div class="dashboard-card green-box">
            <p>Beneficiaries</p>
            <h3>${data.beneficiaries}</h3>
        </div>

        <div class="dashboard-card blue-box">
            <p>Food Donations</p>
            <h3>${data.donations}</h3>
        </div>
        `;
      }

      else if(role==="Donor"){

        cards.innerHTML = `
        <div class="dashboard-card green-box">
            <p>Total Donations</p>
            <h3>${data.donations}</h3>
        </div>

        <div class="dashboard-card blue-box">
            <p>Food Quantity</p>
            <h3>${data.food_quantity}</h3>
        </div>

        <div class="dashboard-card yellow-box">
          <p>Pending Donations</p>
          <h3>${data.pending}</h3>
        </div>

        <div class="dashboard-card red-box">
          <p>Completed Donations</p>
          <h3>${data.completed}</h3>
        </div>
        `;
      }

      else if(role==="Employer"){

        cards.innerHTML = `
        <div class="dashboard-card green-box">
            <p>Jobs Posted</p>
            <h3>${data.jobs}</h3>
        </div>

        <div class="dashboard-card blue-box">
            <p>Applications</p>
            <h3>${data.applications}</h3>
        </div>

        <div class="dashboard-card yellow-box">
            <p>Open Jobs</p>
            <h3>${data.open_jobs || 0}</h3>
        </div>
        `;
      }

      else if(role==="Admin"){

        cards.innerHTML = `
        <div class="dashboard-card green-box">
            <p>Beneficiaries</p>
            <h3>${data.beneficiaries}</h3>
        </div>

        <div class="dashboard-card blue-box">
            <p>Donations</p>
            <h3>${data.donations}</h3>
        </div>

        <div class="dashboard-card yellow-box">
            <p>Jobs</p>
            <h3>${data.jobs}</h3>
        </div>

        <div class="dashboard-card yellow-box">
            <p>Applications</p>
            <h3>${data.applications}</h3>
        </div>
        `;
      }

      // Show statistics chart only for Admin
      if (role === "Admin") {
        document.querySelector(".dashboard-chart").style.display = "block";
        loadDashboardChart(role, data);

        document.getElementById("chartContainer").style.display = "none";
        document.getElementById("chartToggleBtn").innerHTML =
        "📈 Show Statistics";
      }
      else {
        document.querySelector(".dashboard-chart").style.display = "none";
      }

      loadDashboardNotifications();

      loadQuickActions(role);

      // Show dashboard after everything has loaded
      document.getElementById("dashboardLoader").style.display = "none";

      const main = document.getElementById("mainContent");
      main.style.display = "block";

      setTimeout(() => {
          main.classList.add("show");
      }, 50);
  }
  catch(error){
    console.error("Dashboard Error:", error);

    document.getElementById("dashboardLoader").style.display = "none";

    const main = document.getElementById("mainContent");
    main.style.display = "block";

    setTimeout(() => {
        main.classList.add("show");
    }, 50);

    alert(
        "Dashboard failed to load.\n\n" +
        "Open the browser Console (F12) to see the exact error."
    );
  }
}

async function loadDashboardNotifications(){
    const email = localStorage.getItem("email");

    try{
        const response =
        await fetch(
        `${API_BASE_URL}/get_notifications/${email}`
        );

        const notifications =
        await response.json();

        const container =
        document.getElementById("dashboardNotifications");

        if(!container){
          return;
        }

        if(notifications.length===0){

            container.innerHTML=
            "<p>No notifications yet.</p>";

            return;
        }
        let html="";

        notifications
        .slice(0,5)
        .forEach(notification=>{
            html += `
            <div class="dashboard-list-item">
                <div>
                    <strong>
                    🔔 ${notification.title}
                    </strong>
                    <br>
                    <small>
                    ${new Date(notification.time)
                    .toLocaleString()}
                    </small>
                </div>
            </div>
            `;
        });

        html += `
        <div
        class="view-all-link"
        onclick="showNotifications()">

        View All →

        </div>
        `;
        container.innerHTML=html;
    }

    catch(error){
        console.log(error);
    }
}


async function loadDashboardActivity(){
    const email = localStorage.getItem("email");

    try{
        const response =
        await fetch(
        `${API_BASE_URL}/get_activity/${email}`
        );

        const activities =
        await response.json();

        const container =
        document.getElementById("dashboardActivity");

        if(!container){
          return;
        }

        if(activities.length===0){
            container.innerHTML = "<p>No activity yet.</p>";
            return;
        }

        let html = "";

        activities
        .slice(0,5)
        .forEach(activity=>{
            html += `
            <div class="dashboard-list-item">
                <div>
                    <strong>📋 ${activity.description}</strong>
                    <br>
                    <small>
                      ${new Date(activity.time).toLocaleString()}
                    </small>
                </div>
            </div>
            `;
        });

        html += `
        <div
        class="view-all-link"
        onclick="openActivity()">
        View All →
        </div>
        `;
        container.innerHTML = html;
    }

    catch(error){
        console.log(error);
    }
}


async function loadDashboardChart(role){
    const email =
    localStorage.getItem("email");

    const response =
    await fetch(
    `${API_BASE_URL}/dashboard_chart/${role}/${email}`
    );

    const data =
    await response.json();

    const ctx =
    document.getElementById("dashboardChart");

    if(!ctx){
      return;
    }

    if(dashboardChart){
        dashboardChart.destroy();
    }

    let chartType = "bar";

    if(role==="Donor")
        chartType="doughnut";

    if(role==="NGO")
        chartType="pie";

    dashboardChart =
    new Chart(ctx,{

        type:chartType,

        data:{

            labels:data.labels,

            datasets:[{

                label:role,

                data:data.values

            }]

        },

        options:{

            responsive:true,

            plugins:{

                legend:{
                    display:true
                }

            }

        }

    });

}


function loadQuickActions(role){
    const quickActions = document.getElementById("dashboardQuickActions");

    if(!quickActions){
      return;
    }

    let html = "";

    if(role === "Volunteer"){
        html = `
        <button class="primary-btn"
            onclick="window.location.href='beneficiary.html'">
                👤 Register Beneficiary
        </button>

        <button class="primary-btn"
            onclick="window.location.href='jobs.html'">
                💼 View Jobs
        </button>
        `;
    }

    else if(role === "Donor"){
        html = `
        <button class="primary-btn"
            onclick="window.location.href='food-donation.html'">
                🍱 Donate Food
        </button>

        <button class="primary-btn"
            onclick="window.location.href='impact.html'">
                📊 View Impact
        </button>

        `;
    }

    else if(role === "NGO"){
        html = `
        <button class="primary-btn"
            onclick="window.location.href='beneficiary.html'">
                👥 Register Beneficiary
        </button>

        <button class="primary-btn"
            onclick="window.location.href='food-donation.html'">
                🍱 Manage Donations
        </button>
        `;
    }

    else if(role === "Employer"){
        html = `
        <button class="primary-btn">
            💼 Post Job
        </button>

        <button class="primary-btn"
            onclick="window.location.href='jobs.html'">
                📋 View Applications
        </button>
        `;
    }

    else if(role === "Admin"){
        html = `
        <button class="primary-btn"
            onclick="window.location.href='manage-users.html'">
            👥 Manage Users
        </button>

        <button class="primary-btn"
            onclick="window.location.href='impact.html'">
                📊 Platform Reports
        </button>
        `;
    }

    const container =
        document.getElementById("dashboardNotifications");
        console.log(container);

    quickActions.innerHTML = html;
}


function updateDashboardSummary(role, data){
    // Notifications
    document.getElementById(
        "summaryNotifications"
    ).innerText =
    data.notifications || 0;

    // Today's Activity
    document.getElementById(
        "summaryActivity"
    ).innerText =
    data.today_activity || 0;


    // Pending Tasks
    let pending = 0;

    if(role==="Volunteer"){

        pending =
        data.pending_beneficiaries || 0;

    }

    else if(role==="Donor"){

        pending =
        data.pending || 0;

    }

    else if(role==="NGO"){

        pending =
        data.pending_beneficiaries || 0;

    }

    else if(role==="Employer"){

        pending =
        data.open_jobs || 0;

    }

    else if(role==="Admin"){

        pending =
        data.applications || 0;

    }

    document.getElementById(
        "summaryPending"
    ).innerText = pending;


    // Performance
    let performance = "--";

    if(role==="Donor"){

        if(data.donations>0){

            performance =
            Math.round(
            (data.completed/data.donations)*100
            ) + "%";

        }
        else{

            performance="0%";

        }

    }

    else if(role==="Volunteer"){

        performance =
        data.applications + " Jobs";

    }

    else if(role==="NGO"){

        performance =
        data.beneficiaries + " Served";

    }

    else if(role==="Employer"){

        performance =
        data.jobs + " Jobs";

    }

    else if(role==="Admin"){

        performance =
        data.users + " Users";

    }

    document.getElementById(
        "summaryPerformance"
    ).innerText =
    performance;

}


/* Dashboard Click */
function openDashboard(){
    const role = localStorage.getItem("role");

    if(!role){
        alert("Please Login First");
        return;
    }

    localStorage.setItem(
        "dashboardPreviousPage",
        window.location.href
    );

    window.location.href = "dashboard.html";

    document.getElementById("mainContent")
    .classList.remove("blur-bg");   // REMOVE BLUR HERE
}


function closeDashboard(){
    const previousPage = localStorage.getItem("dashboardPreviousPage");

    if(previousPage){
        localStorage.removeItem("dashboardPreviousPage");
        window.location.href = previousPage;
    }
    else{
        window.location.href = "home.html";
    }
}


/* LOAD DASHBOARD PAGE */
window.addEventListener("load", ()=>{

    const loginRole =
    localStorage.getItem("role");

   const activeRole = localStorage.getItem("role");

    if(!loginRole){

        alert("Please Login First");

        window.location.href =
        "Sparc.html";

        return;
    }


    let dashboardRole =
    loginRole;


    /* ADMIN CAN VIEW SELECTED ROLE */

    if(
        loginRole === "Admin"
        &&
        activeRole
    ){

        dashboardRole =
        activeRole;

    }


    /* NORMAL USERS VIEW OWN ROLE */

    if(
        loginRole !== "Admin"
    ){

        dashboardRole =
        loginRole;

    }


    loadDashboard(
        dashboardRole
    );

});

