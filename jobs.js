/* let selectedJobId = null;

function openJobModal(jobId){

    selectedJobId = jobId;

    document.getElementById(
    "jobApplyModal").style.display = "flex";
} 

function closeJobModal(){

    document.getElementById(
    "jobApplyModal").style.display =
    "none";
}

async function submitJobApplication(){

    const name =
    document.getElementById(
    "applicantName").value;

    const phone =
    document.getElementById(
    "applicantPhone").value;
    
    if(!/^\d{10}$/.test(phone)){
        alert("Please enter a valid 10-digit phone number");
        return;
    }
    
    const skills =
    document.getElementById(
    "applicantSkills").value;

    if(!name || !phone || !skills){

        alert("Fill all fields");
        return;
    }

    try{

        const response =
        await fetch(
        `${API_BASE_URL}/apply_job`,
        {
            method:"POST",

            headers:{
                "Content-Type":
                "application/json"
            },

            body:JSON.stringify({
                email:localStorage.getItem("email"),
                job_id:selectedJobId,
                name:name,
                phone:phone,
                skills:skills
            })
        });

        const data = await response.json();

        if(response.ok){
            closeJobModal();
            showJobPopup();
        }
        else{
            alert(data.message || "Application Failed");
            return;
        }

        document.getElementById(
        "applicantName").value="";

        document.getElementById(
        "applicantPhone").value="";

        document.getElementById(
        "applicantSkills").value="";

    }
    catch(error){

        console.log(error);

        alert("Backend Error");
    }
}

function showJobPopup(){

    document.getElementById(
    "jobPopup").style.display =
    "flex";
}

function closeJobPopup(){

    document.getElementById(
    "jobPopup").style.display =
    "none";
} */


let selectedJobId = null;

let selectedLivelihoodPath = "IMMEDIATE_INCOME";

let allJobs = [];

let currentEmployerApplications = [];

// ============================================================
// PAGE LOAD
document.addEventListener("DOMContentLoaded", () => {
    initializeJobPage();

});

// ============================================================
// INITIALIZE JOB PAGE
async function initializeJobPage(){
    const role =
        localStorage.getItem("role");

    // --------------------------------------------------------
    // EMPLOYER CONTROLS
    // --------------------------------------------------------
    if(role === "Employer"){
        const employerControls =
            document.getElementById(
                "employerControls"
            );

        if(employerControls){
            employerControls.style.display =
                "flex";
        }
    }

    // --------------------------------------------------------
    // BENEFICIARY CONTROLS
    // --------------------------------------------------------
    if(role === "Beneficiary"){
        const beneficiaryOfferControls =
            document.getElementById(
                "beneficiaryOfferControls"
            );

        if(beneficiaryOfferControls){
            beneficiaryOfferControls.style.display =
                "flex";
        }
    }

    // --------------------------------------------------------
    // ADMIN CONTROLS
    if(role === "Admin"){
        const adminControls =
            document.getElementById(
                "adminControls"
            );

        if(adminControls){
            adminControls.style.display =
                "flex";
        }
    }

    await loadJobs();

    if(
        role === "Volunteer" ||
        role === "NGO" ||
        role === "Admin"
    ){
        const assistedOfferControls =
            document.getElementById(
                "assistedOfferControls"
            );

        if(assistedOfferControls){
            assistedOfferControls.style.display =
                "flex";
        }
    }
}


// ============================================================
// LOAD JOBS FROM BACKEND
// ============================================================
async function loadJobs(){
    const container =
        document.getElementById(
            "jobsContainer"
        );

    const emptyState =
        document.getElementById(
            "jobsEmptyState"
        );

    if(!container){
        return;
    }

    container.innerHTML =
        `<div class="job-loading">
            Loading opportunities...
        </div>`;

    emptyState.style.display =
        "none";

    try{
        const response =
            await fetch(
                `${API_BASE_URL}/get_jobs`
            );

        const data =
            await response.json();

        if(!response.ok || !data.success){
            throw new Error(
                data.message ||
                "Unable to load jobs."
            );
        }

        allJobs =
            data.jobs || [];

        renderJobs();
    }

    catch(error){
        console.error(
            "Job loading error:",
            error
        );

        container.innerHTML = `
            <div class="job-error">
                <span class="material-symbols-outlined">
                    error
                </span>

                <h3>
                    Unable to load opportunities
                </h3>

                <p>
                    Please try again.
                </p>

                <button
                    class="primary-btn"
                    onclick="loadJobs()">

                    Retry

                </button>
            </div>
        `;
    }
}


// ============================================================
// SHOW LIVELIHOOD PATH
// ============================================================

function showLivelihoodPath(path){

    selectedLivelihoodPath =
        path;


    const immediateBtn =
        document.getElementById(
            "immediateIncomeBtn"
        );

    const careerBtn =
        document.getElementById(
            "careerGrowthBtn"
        );


    immediateBtn.classList.remove(
        "active"
    );

    careerBtn.classList.remove(
        "active"
    );


    if(path === "IMMEDIATE_INCOME"){

        immediateBtn.classList.add(
            "active"
        );

        document.getElementById(
            "jobPathTitle"
        ).textContent =
            "Immediate Income Opportunities";

        document.getElementById(
            "jobPathDescription"
        ).textContent =
            "Daily and short-term work opportunities for people who need income now.";

    }

    else{

        careerBtn.classList.add(
            "active"
        );

        document.getElementById(
            "jobPathTitle"
        ).textContent =
            "Career Growth Opportunities";

        document.getElementById(
            "jobPathDescription"
        ).textContent =
            "Skilled jobs, apprenticeships and long-term employment opportunities.";

    }


    renderJobs();

}


// ============================================================
// RENDER JOBS
// ============================================================

function renderJobs(){

    const container =
        document.getElementById(
            "jobsContainer"
        );

    const emptyState =
        document.getElementById(
            "jobsEmptyState"
        );


    const filteredJobs =
        allJobs.filter(
            job =>
                job.livelihood_path ===
                selectedLivelihoodPath
        );


    container.innerHTML = "";


    if(filteredJobs.length === 0){

        emptyState.style.display =
            "block";

        return;

    }


    emptyState.style.display =
        "none";


    filteredJobs.forEach(
        job => {

            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "job-card card-hover";


            const icon =
                selectedLivelihoodPath ===
                "IMMEDIATE_INCOME"
                    ? "work"
                    : "trending_up";


            const wageText = 
                formatWage(
                    job
                );


            const workDate =
                job.work_date
                    ? formatDate(
                        job.work_date
                    )
                    : "Flexible date";


            card.innerHTML = `

                <span class="material-symbols-outlined">
                    ${icon}
                </span>

                <h3>
                    ${escapeHtml(
                        job.title
                    )}
                </h3>

                <p>
                    ${escapeHtml(
                        wageText
                    )}
                </p>

                <p>
                    📍 ${escapeHtml(
                        job.location ||
                        "Location not specified"
                    )}
                </p>

                <p>
                    📅 ${escapeHtml(
                        workDate
                    )}
                </p>

                <button
                    class="primary-btn"
                    style="margin-top:24px;"
                    onclick="openJobDetails(${job.id})">

                    View Opportunity

                </button>

            `;


            container.appendChild(
                card
            );

        }
    );

}


// ============================================================
// FORMAT WAGE
// ============================================================

function formatWage(job){

    const amount =
        job.wage_amount;

    if(amount === null ||
       amount === undefined){

        return "Wage to be discussed";

    }


    const formatted =
        Number(amount).toLocaleString(
            "en-IN"
        );


    switch(job.wage_type){

        case "HOURLY":
            return `₹${formatted}/hour`;

        case "MONTHLY":
            return `₹${formatted}/month`;

        case "PROJECT":
            return `₹${formatted}/project`;

        default:
            return `₹${formatted}/day`;

    }

}


// ============================================================
// JOB DETAILS
// ============================================================

function openJobDetails(jobId){

    const job =
        allJobs.find(
            item =>
                Number(item.id) ===
                Number(jobId)
        );


    if(!job){

        alert(
            "Job information not found."
        );

        return;

    }


    selectedJobId =
        jobId;


    const content =
        document.getElementById(
            "jobDetailsContent"
        );


    const employerName =
        job.employer_name ||
        "Verified SPARC Employer";


    content.innerHTML = `

        <span class="material-symbols-outlined job-detail-icon">
            work
        </span>

        <h2>
            ${escapeHtml(
                job.title
            )}
        </h2>

        <p class="job-employer">
            ${escapeHtml(
                employerName
            )}
        </p>


        <div class="job-detail-grid">

            <div>
                <strong>Opportunity Type</strong>
                <span>
                    ${
                        job.livelihood_path ===
                        "IMMEDIATE_INCOME"
                            ? "Immediate Income"
                            : "Career Growth"
                    }
                </span>
            </div>


            <div>
                <strong>Wage</strong>
                <span>
                    ${escapeHtml(
                        formatWage(job)
                    )}
                </span>
            </div>


            <div>
                <strong>Location</strong>
                <span>
                    ${escapeHtml(
                        job.location ||
                        "Not specified"
                    )}
                </span>
            </div>


            <div>
                <strong>Work Date</strong>
                <span>
                    ${
                        job.work_date
                            ? formatDate(
                                job.work_date
                            )
                            : "Flexible"
                    }
                </span>
            </div>


            <div>
                <strong>Working Hours</strong>
                <span>
                    ${
                        job.start_time &&
                        job.end_time
                            ? escapeHtml(
                                formatTime(
                                    job.start_time
                                )
                            ) +
                              " - " +
                              escapeHtml(
                                formatTime(
                                    job.end_time
                                )
                              )
                            : "Not specified"
                    }
                </span>
            </div>


            <div>
                <strong>Payment</strong>
                <span>
                    ${escapeHtml(
                        formatPaymentCommitment(
                            job.payment_commitment
                        )
                    )}
                </span>
            </div>


            <div>
                <strong>Vacancies</strong>
                <span>
                    ${job.vacancies || 1}
                </span>
            </div>


            <div>
                <strong>Meeting Point</strong>
                <span>
                    ${escapeHtml(
                        job.meeting_point ||
                        "Same as work location"
                    )}
                </span>
            </div>

        </div>


        <div class="job-description">

            <h3>
                About the Work
            </h3>

            <p>
                ${escapeHtml(
                    job.description ||
                    "No description provided."
                )}
            </p>

        </div>


        ${
            job.requirements
            ? `
                <div class="job-description">

                    <h3>
                        Requirements
                    </h3>

                    <p>
                        ${escapeHtml(
                            job.requirements
                        )}
                    </p>

                </div>
            `
            : ""
        }


        <button
            class="primary-btn login-btn"
            onclick="openJobApplication(${job.id})">

            Apply for This Opportunity

        </button>

    `;


    document.getElementById(
        "jobDetailsModal"
    ).style.display =
        "flex";

}


// ============================================================
// CLOSE JOB DETAILS
// ============================================================

function closeJobDetails(){

    document.getElementById(
        "jobDetailsModal"
    ).style.display =
        "none";

}


// ============================================================
// OPEN APPLICATION
// ============================================================

async function openJobApplication(jobId){

    selectedJobId =
        jobId;


    const job =
        allJobs.find(
            item =>
                Number(item.id) ===
                Number(jobId)
        );


    if(!job){
        return;
    }


    document.getElementById(
        "applicationJobTitle"
    ).textContent =
        job.title;


    closeJobDetails();


    const role =
        localStorage.getItem(
            "role"
        );


    const selfArea =
        document.getElementById(
            "selfApplicationArea"
        );

    const assistedArea =
        document.getElementById(
            "assistedApplicationArea"
        );


    /*
     * Beneficiary:
     * Self application
     */
    if(role === "Beneficiary"){

        selfArea.style.display =
            "block";

        assistedArea.style.display =
            "none";

    }


    /*
     * Volunteer / NGO:
     * Assisted application
     */
    else if(
        role === "Volunteer" ||
        role === "NGO" ||
        role === "Admin"
    ){

        selfArea.style.display =
            "none";

        assistedArea.style.display =
            "block";

        await loadAssistedBeneficiaries();

    }


    /*
     * Other roles:
     * No beneficiary application access.
     */
    else{

        selfArea.style.display =
            "none";

        assistedArea.style.display =
            "none";

        alert(
            "Only beneficiaries or authorized Volunteer/NGO staff can apply for livelihood opportunities."
        );

        return;

    }


    document.getElementById(
        "jobApplyModal"
    ).style.display =
        "flex";

}


// ============================================================
// CLOSE APPLICATION
// ============================================================

function closeJobModal(){

    document.getElementById(
        "jobApplyModal"
    ).style.display =
        "none";

}


// ============================================================
// SELF APPLICATION
// ============================================================

async function submitSelfApplication(){

    const email =
        localStorage.getItem(
            "email"
        );


    if(!email){

        alert(
            "Please log in first."
        );

        return;

    }


    try{

        const profileResponse =
            await fetch(
                `${API_BASE_URL}/my_beneficiary_profile/${encodeURIComponent(email)}`
            );


        const profileData =
            await profileResponse.json();


        if(
            !profileResponse.ok ||
            !profileData.success
        ){

            alert(
                profileData.message ||
                "No beneficiary profile is linked to your account."
            );

            return;

        }


        const beneficiaryId =
            profileData.beneficiary.id;


        const response =
            await fetch(
                `${API_BASE_URL}/apply_job`,
                {
                    method:"POST",

                    headers:{
                        "Content-Type":
                            "application/json"
                    },

                    body:JSON.stringify({

                        job_id:
                            selectedJobId,

                        beneficiary_id:
                            beneficiaryId,

                        application_source:
                            "SELF",

                        submitted_by_email:
                            email
                    })
                }
            );

        const data =
            await response.json();


        if(response.ok){

            closeJobModal();

            showJobPopup(
                "Application Submitted",
                "Your application has been submitted successfully."
            );

        }

        else{

            alert(
                data.message ||
                "Application failed."
            );

        }

    }

    catch(error){

        console.error(
            error
        );

        alert(
            "Unable to submit application."
        );

    }

}


// ============================================================
// LOAD BENEFICIARIES FOR ASSISTED APPLICATION
// ============================================================

async function loadAssistedBeneficiaries(){

    const select =
        document.getElementById(
            "assistedBeneficiarySelect"
        );


    select.innerHTML =
        `<option value="">
            Loading beneficiaries...
        </option>`;


    const email =
        localStorage.getItem(
            "email"
        );


    try{

        /*
         * We use the existing beneficiary listing
         * endpoint for now.
         *
         * The backend will later be restricted
         * further by authenticated role.
         */
        const response =
            await fetch(
                `${API_BASE_URL}/get_beneficiaries?email=${encodeURIComponent(email)}`
            );

        const data =
            await response.json();

        if(!response.ok){
            throw new Error(
                data.message ||
                "Unable to load beneficiaries."
            );
        }

        const beneficiaries =
            data.beneficiaries ||
            [];

        select.innerHTML =
            `<option value="">
                Select Beneficiary
            </option>`;

        beneficiaries.forEach(
            beneficiary => {

                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    beneficiary.id;

                option.textContent =
                    `${beneficiary.full_name} — ${beneficiary.location || "Location not specified"}`;

                select.appendChild(
                    option
                );
            }
        );

        if(
            beneficiaries.length === 0
        ){

            select.innerHTML =
                `<option value="">
                    No beneficiaries found
                </option>`;

        }

    }

    catch(error){

        console.error(
            error
        );

        select.innerHTML =
            `<option value="">
                Unable to load beneficiaries
            </option>`;

    }

}


// ============================================================
// ASSISTED APPLICATION
// ============================================================

async function submitAssistedApplication(){

    const beneficiaryId =
        document.getElementById(
            "assistedBeneficiarySelect"
        ).value;


    const submittedByEmail =
        localStorage.getItem(
            "email"
        );


    if(!beneficiaryId){

        alert(
            "Please select a beneficiary."
        );

        return;

    }


    if(!submittedByEmail){

        alert(
            "Please log in again."
        );

        return;

    }


    try{

        const response =
            await fetch(
                `${API_BASE_URL}/apply_job`,
                {
                    method:"POST",

                    headers:{
                        "Content-Type":
                            "application/json"
                    },

                    body:JSON.stringify({

                        job_id:
                            selectedJobId,

                        beneficiary_id:
                            Number(
                                beneficiaryId
                            ),

                        application_source:
                            "ASSISTED",

                        submitted_by_email:
                            submittedByEmail

                    })

                }
            );


        const data =
            await response.json();


        if(response.ok){

            closeJobModal();

            showJobPopup(
                "Application Submitted",
                "The beneficiary has been successfully applied for this opportunity."
            );

        }

        else{

            alert(
                data.message ||
                "Application failed."
            );

        }

    }

    catch(error){

        console.error(
            error
        );

        alert(
            "Unable to submit application."
        );

    }

}


// ============================================================
// EMPLOYER: OPEN POST JOB
// ============================================================

function openPostJobModal(){

    document.getElementById(
        "postJobModal"
    ).style.display =
        "flex";

}


// ============================================================
// EMPLOYER: CLOSE POST JOB
// ============================================================

function closePostJobModal(){

    document.getElementById(
        "postJobModal"
    ).style.display =
        "none";

}


// ============================================================
// EMPLOYER: SUBMIT JOB
// ============================================================

async function submitNewJob(){

    const employerEmail =
        localStorage.getItem(
            "email"
        );


    const title =
        document.getElementById(
            "jobTitle"
        ).value.trim();


    const description =
        document.getElementById(
            "jobDescription"
        ).value.trim();


    const livelihoodPath =
        document.getElementById(
            "jobLivelihoodPath"
        ).value;


    const wageType =
        document.getElementById(
            "jobWageType"
        ).value;


    const wageAmount =
        document.getElementById(
            "jobWageAmount"
        ).value;


    const vacancies =
        document.getElementById(
            "jobVacancies"
        ).value;


    const workDate =
        document.getElementById(
            "jobWorkDate"
        ).value;


    const startTime =
        document.getElementById(
            "jobStartTime"
        ).value;


    const endTime =
        document.getElementById(
            "jobEndTime"
        ).value;


    const location =
        document.getElementById(
            "jobLocation"
        ).value.trim();


    const meetingPoint =
        document.getElementById(
            "jobMeetingPoint"
        ).value.trim();


    const paymentCommitment =
        document.getElementById(
            "jobPaymentCommitment"
        ).value;


    const requirements =
        document.getElementById(
            "jobRequirements"
        ).value.trim();


    if(
        !employerEmail ||
        !title ||
        !description ||
        !location ||
        !wageAmount ||
        !vacancies
    ){

        alert(
            "Please fill all required job details."
        );

        return;

    }


    if(
        Number(wageAmount) <= 0
    ){

        alert(
            "Wage amount must be greater than zero."
        );

        return;

    }


    try{

        const response =
            await fetch(
                `${API_BASE_URL}/post_job`,
                {
                    method:"POST",

                    headers:{
                        "Content-Type":
                            "application/json"
                    },

                    body:JSON.stringify({

                        employer_email:
                            employerEmail,

                        title:
                            title,

                        description:
                            description,

                        livelihood_path:
                            livelihoodPath,

                        wage_type:
                            wageType,

                        wage_amount:
                            Number(
                                wageAmount
                            ),

                        vacancies:
                            Number(
                                vacancies
                            ),

                        work_date:
                            workDate || null,

                        start_time:
                            startTime || null,

                        end_time:
                            endTime || null,

                        location:
                            location,

                        meeting_point:
                            meetingPoint || null,

                        payment_commitment:
                            paymentCommitment,

                        requirements:
                            requirements || null

                    })

                }
            );


        const data =
            await response.json();


        if(response.ok){

            closePostJobModal();

            clearPostJobForm();

            await loadJobs();

            showJobPopup(
                "Job Posted",
                "Your job opportunity has been posted successfully."
            );

        }

        else{

            alert(
                data.message ||
                "Unable to post job."
            );

        }

    }

    catch(error){

        console.error(
            error
        );

        alert(
            "Unable to connect to the server."
        );

    }

}


// ============================================================
// CLEAR POST JOB FORM
// ============================================================

function clearPostJobForm(){

    [
        "jobTitle",
        "jobDescription",
        "jobWageAmount",
        "jobWorkDate",
        "jobStartTime",
        "jobEndTime",
        "jobLocation",
        "jobMeetingPoint",
        "jobRequirements"
    ].forEach(
        id => {

            const element =
                document.getElementById(
                    id
                );

            if(element){

                element.value =
                    "";

            }

        }
    );


    document.getElementById(
        "jobVacancies"
    ).value = "1";


    document.getElementById(
        "jobLivelihoodPath"
    ).value =
        "IMMEDIATE_INCOME";


    document.getElementById(
        "jobWageType"
    ).value =
        "DAILY";


    document.getElementById(
        "jobPaymentCommitment"
    ).value =
        "END_OF_DAY";

}


// ============================================================
// EMPLOYER: LOAD APPLICATIONS
// ============================================================
async function loadEmployerApplications(){
    const employerEmail =
        localStorage.getItem(
            "email"
        );


    if(!employerEmail){
        alert(
            "Please log in again."
        );
        return;
    }


    document.getElementById(
        "applicantsModal"
    ).style.display =
        "flex";


    const container =
        document.getElementById(
            "applicantsContainer"
        );


    container.innerHTML =
        "Loading applicants...";


    try{
        const email =
            localStorage.getItem(
                "email"
            );

        const response =
            await fetch(
                `${API_BASE_URL}/get_applications?email=${encodeURIComponent(email)}`
            );

        const data =
            await response.json();

        if(
            !response.ok ||
            !data.success
        ){

            throw new Error(
                data.message ||
                "Unable to load applicants."
            );
        }

        currentEmployerApplications =
            data.applications || [];

        renderEmployerApplications(
            currentEmployerApplications
        );
    }

    catch(error){
        console.error(
            error
        );

        container.innerHTML = `
            <div class="job-error">
                Unable to load applicants.
            </div>
        `;
    }
}


// ============================================================
// RENDER EMPLOYER APPLICATIONS
// ============================================================

function renderEmployerApplications(
    applications
){

    const container =
        document.getElementById(
            "applicantsContainer"
        );


    if(applications.length === 0){

        container.innerHTML = `
            <div class="job-empty-state">
                <span class="material-symbols-outlined">
                    group_off
                </span>

                <h3>
                    No applications yet
                </h3>

                <p>
                    Applicants will appear here
                    when beneficiaries apply.
                </p>
            </div>
        `;

        return;

    }

    container.innerHTML =
        "";

    applications.forEach(
        application => {
            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "applicant-card";

            const status =
                application.application_status ||
                "Pending";

            card.innerHTML = `
                <div class="applicant-card-header">
                    <div>
                        <h3>
                            ${escapeHtml(
                                application.beneficiary_name ||
                                application.applicant_name ||
                                "Applicant"
                            )}
                        </h3>

                        <p>
                            ${escapeHtml(
                                application.job_title
                            )}
                        </p>
                    </div>

                    <span class="application-status">
                        ${escapeHtml(
                            status
                        )}
                    </span>
                </div>

                <div class="applicant-details">
                    <p>
                        📍
                        <strong>Locality:</strong>
                        ${escapeHtml(
                            application.beneficiary_location ||
                            "Location not provided"
                        )}
                    </p>

                    <p>
                        📞
                        <strong>Contact:</strong>
                        ${escapeHtml(
                            application.beneficiary_phone ||
                            application.applicant_phone ||
                            "Not provided"
                        )}
                    </p>

                    <p>
                        🎓
                        <strong>Education:</strong>
                        ${escapeHtml(
                            application.beneficiary_education ||
                            "Not specified"
                        )}
                    </p>

                    <p>
                        🛠
                        <strong>Skills:</strong>
                        ${escapeHtml(
                            application.beneficiary_skills ||
                            application.applicant_skills ||
                            "Not specified"
                        )}
                    </p>

                    <p>
                        💼
                        <strong>Experience:</strong>
                        ${
                            application.beneficiary_experience ??
                            "Not specified"
                        }
                        ${
                            application.beneficiary_experience !== null &&
                            application.beneficiary_experience !== undefined
                                ? " years"
                                : ""
                        }
                    </p>

                    <p>
                        📅
                        <strong>Applied On:</strong>
                        ${formatDateTime(
                            application.applied_at
                        )}
                    </p>

                    <p>
                        👤
                        <strong>Application Type:</strong>
                        ${
                            application.application_source === "SELF"
                            ? "Beneficiary applied directly"
                            : "Volunteer / NGO assisted"
                        }
                    </p>

                    ${
                        application.application_source === "ASSISTED"
                            ? `
                                <p>
                                    🤝
                                    <strong>Submitted By:</strong>
                                    ${escapeHtml(
                                        application.submitted_by_email ||
                                        "Not available"
                                    )}
                                </p>
                            `
                            : ""
                    }

                    <p>
                        💰
                        <strong>Job Wage:</strong>
                        ${escapeHtml(
                            formatWage({
                                wage_amount:
                                    application.wage_amount,
                                wage_type:
                                    application.wage_type
                            })
                        )}
                    </p>

                    <p>
                        💳
                        <strong>Payment:</strong>
                        ${escapeHtml(
                            formatPaymentCommitment(
                                application.payment_commitment
                            )
                        )}
                    </p>
                </div>

                <div class="applicant-actions">
                    ${
                        status === "Pending"
                            ? `
                                <button
                                    class="secondary-btn"
                                    onclick="shortlistApplication(${application.id})">

                                    Shortlist

                                </button>

                                <button
                                    class="danger-btn"
                                    onclick="rejectApplication(${application.id})">

                                    Reject

                                </button>
                            `
                            : ""
                    }

                    ${
                        status === "Shortlisted"
                            ? `
                                <button
                                    class="primary-btn"
                                    onclick="sendJobOffer(${application.id})">

                                    Select & Send Offer

                                </button>

                                <button
                                    class="danger-btn"
                                    onclick="rejectApplication(${application.id})">

                                    Reject

                                </button>
                            `
                            : ""
                    }

                    ${
                        status === "Selected"
                            ? `
                                <span class="application-info">
                                    Job offer already sent.
                                </span>
                            `
                            : ""
                    }
                </div>
            `;

            container.appendChild(
                card
            );
        }
    );
}


// ============================================================
// SHORTLIST
// ============================================================
async function shortlistApplication(
    applicationId
){
    const employerEmail =
        localStorage.getItem(
            "email"
        );

    await employerApplicationAction(
        `/shortlist_application/${applicationId}`,
        employerEmail,
        "Applicant shortlisted successfully."
    );
}


// ============================================================
// REJECT
// ============================================================
async function rejectApplication(
    applicationId
){

    const employerEmail =
        localStorage.getItem(
            "email"
        );

    if(
        !confirm(
            "Are you sure you want to reject this application?"
        )
    ){
        return;
    }

    await employerApplicationAction(
        `/reject_application/${applicationId}`,
        employerEmail,
        "Application rejected."
    );
}


// ============================================================
// GENERIC EMPLOYER APPLICATION ACTION
// ============================================================
async function employerApplicationAction(
    endpoint,
    employerEmail,
    successMessage
){

    try{
        const response =
            await fetch(
                `${API_BASE_URL}${endpoint}`,
                {
                    method:"POST",

                    headers:{
                        "Content-Type":
                            "application/json"
                    },

                    body:JSON.stringify({
                        employer_email:
                            employerEmail
                    })
                }
            );

        const data =
            await response.json();

        if(response.ok){
            alert(
                successMessage
            );

            await loadEmployerApplications();
        }

        else{
            alert(
                data.message ||
                "Action failed."
            );
        }
    }

    catch(error){
        console.error(
            error
        );

        alert(
            "Unable to connect to server."
        );
    }
}


// ============================================================
// SEND JOB OFFER
// ============================================================
// ============================================================
// OPEN JOB OFFER CONFIRMATION
// ============================================================
let selectedApplicationForOffer = null;


async function sendJobOffer(
    applicationId
){

    const application =
        currentEmployerApplications.find(
            item =>
                Number(item.id) ===
                Number(applicationId)
        );

    if(!application){
        alert(
            "Application details not found."
        );

        return;
    }

    selectedApplicationForOffer =
        application;

    const details =
        document.getElementById(
            "jobOfferDetails"
        );

    details.innerHTML = `
        <div class="applicant-details">
            <p>
                <strong>Beneficiary:</strong>
                ${escapeHtml(
                    application.beneficiary_name ||
                    application.applicant_name ||
                    "Applicant"
                )}
            </p>

            <p>
                <strong>Job:</strong>
                ${escapeHtml(
                    application.job_title ||
                    "Job"
                )}
            </p>

            <p>
                <strong>Wage:</strong>
                ${escapeHtml(
                    formatWage({
                        wage_amount:
                            application.wage_amount,
                        wage_type:
                            application.wage_type
                    })
                )}
            </p>

            <p>
                <strong>Work Date:</strong>
                ${
                    application.work_date
                        ? formatDate(
                            application.work_date
                        )
                        : "Flexible"
                }
            </p>

            <p>
                <strong>Work Location:</strong>
                ${escapeHtml(
                    application.job_location ||
                    application.beneficiary_location ||
                    "Not specified"
                )}
            </p>

            <p>
                <strong>Meeting Point:</strong>
                ${escapeHtml(
                    application.meeting_point ||
                    "Same as work location"
                )}
            </p>

            <p>
                <strong>Payment:</strong>
                ${escapeHtml(
                    formatPaymentCommitment(
                        application.payment_commitment
                    )
                )}
            </p>
        </div>
    `;

    document.getElementById(
        "offerMessage"
    ).value = "";

    document.getElementById(
        "jobOfferModal"
    ).style.display =
        "flex";
}


// ============================================================
// CONFIRM SEND JOB OFFER
// ============================================================
async function confirmSendJobOffer(){
    const application =
        selectedApplicationForOffer;

    if(!application){
        alert(
            "No applicant selected."
        );
        return;
    }

    const employerEmail =
        localStorage.getItem(
            "email"
        );

    if(!employerEmail){
        alert(
            "Please log in again."
        );
        return;
    }

    const offerMessage =
        document.getElementById(
            "offerMessage"
        ).value.trim();

    if(
        !confirm(
            "Confirm that you are offering this job at the displayed wage and payment schedule?"
        )
    ){
        return;
    }

    try{
        const response =
            await fetch(
                `${API_BASE_URL}/send_job_offer`,
                {
                    method:"POST",

                    headers:{
                        "Content-Type":
                            "application/json"
                    },

                    body:JSON.stringify({
                        application_id:
                            application.id,

                        employer_email:
                            employerEmail,

                        offer_message:
                            offerMessage
                    })
                }
            );

        const data =
            await response.json();

        if(!response.ok){
            alert(
                data.message ||
                "Unable to send job offer."
            );
            return;
        }

        closeJobOfferModal();

        alert(
            "Job offer sent successfully."
        );

        await loadEmployerApplications();
    }

    catch(error){
        console.error(error);
        alert(
            "Unable to connect to server."
        );
    }
}


function closeJobOfferModal(){
    document.getElementById(
        "jobOfferModal"
    ).style.display =
        "none";

    selectedApplicationForOffer =
        null;
}


// ============================================================
// CLOSE APPLICANTS
// ============================================================
function closeApplicantsModal(){
    document.getElementById(
        "applicantsModal"
    ).style.display =
        "none";
}


// ============================================================
// SUCCESS POPUP
// ============================================================
function showJobPopup(
    title,
    message
){
    document.getElementById(
        "jobPopupTitle"
    ).textContent =
        title;

    document.getElementById(
        "jobPopupMessage"
    ).textContent =
        message;

    document.getElementById(
        "jobPopup"
    ).style.display =
        "flex";
}


function closeJobPopup(){
    document.getElementById(
        "jobPopup"
    ).style.display =
        "none";
}


// ============================================================
// FORMATTING HELPERS
// ============================================================

function formatDate(
    dateString
){

    if(!dateString){
        return "Not specified";
    }

    const date =
        new Date(
            dateString +
            "T00:00:00"
        );

    return date.toLocaleDateString(
        "en-IN",
        {
            day:"2-digit",
            month:"short",
            year:"numeric"
        }
    );
}


function formatDateTime(
    dateString
){

    if(!dateString){
        return "Not available";
    }

    const date =
        new Date(
            dateString
        );

    return date.toLocaleDateString(
        "en-IN",
        {
            day:"2-digit",
            month:"short",
            year:"numeric"
        }
    );
}


function formatTime(
    timeString
){
    if(!timeString){
        return "";
    }

    const parts =
        timeString.split(":");

    let hour =
        Number(
            parts[0]
        );

    const minute =
        parts[1] || "00";

    const period =
        hour >= 12
            ? "PM"
            : "AM";

    hour =
        hour % 12 || 12;

    return `${hour}:${minute} ${period}`;
}


function formatPaymentCommitment(
    commitment
){
    const values = {
        END_OF_DAY:
            "Payment at end of day",

        WITHIN_24_HOURS:
            "Payment within 24 hours",

        WEEKLY:
            "Weekly payment",

        MONTHLY:
            "Monthly payment",

        OTHER:
            "Payment schedule specified by employer"
    };

    return values[commitment] ||
           "Payment schedule not specified";
}


// ============================================================
// HTML SAFETY
// ============================================================
function escapeHtml(
    value
){

    if(
        value === null ||
        value === undefined
    ){
        return "";
    }

    return String(value)
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );
}


// ============================================================
// LOAD MY JOB OFFERS
// ============================================================
async function loadMyJobOffers(){
    const email =
        localStorage.getItem("email");

    if(!email){
        alert(
            "Please log in again."
        );
        return;
    }

    document.getElementById(
        "jobOffersModal"
    ).style.display =
        "flex";

    const container =
        document.getElementById(
            "jobOffersContainer"
        );

    container.innerHTML =
        "Loading offers...";

    try{
        const response =
            await fetch(
                `${API_BASE_URL}/get_job_offers?email=${encodeURIComponent(email)}`
            );

        const data =
            await response.json();

        if(
            !response.ok ||
            !data.success
        ){
            throw new Error(
                data.message ||
                "Unable to load job offers."
            );
        }

        renderMyJobOffers(
            data.offers || []
        );
    }

    catch(error){
        console.error(error);

        container.innerHTML = `
            <div class="job-error">

                <span class="material-symbols-outlined">
                    error
                </span>

                <h3>
                    Unable to load offers
                </h3>

                <p>
                    ${escapeHtml(
                        error.message
                    )}
                </p>
            </div>
        `;
    }
}


// ============================================================
// RENDER JOB OFFERS
// ============================================================
function renderMyJobOffers(
    offers
){
    const container =
        document.getElementById(
            "jobOffersContainer"
        );

    if(offers.length === 0){
        container.innerHTML = `
            <div class="job-empty-state">

                <span class="material-symbols-outlined">
                    mail
                </span>

                <h3>
                    No pending job offers
                </h3>

                <p>
                    New offers from employers
                    will appear here.
                </p>
            </div>
        `;
        return;
    }

    container.innerHTML =
        "";

    offers.forEach(
        offer => {
            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "applicant-card";

            card.innerHTML = `
                <div class="applicant-card-header">
                    <div>
                        <h3>
                            ${escapeHtml(
                                offer.job_title
                            )}
                        </h3>

                        <p>
                            Employer:
                            ${escapeHtml(
                                offer.employer_name ||
                                "SPARC Employer"
                            )}
                        </p>
                    </div>

                    <span class="application-status">
                        Offer Received
                    </span>
                </div>

                <div class="applicant-details">
                    <p>
                        💰
                        <strong>Wage:</strong>
                        ₹${Number(
                            offer.offered_wage
                        ).toLocaleString("en-IN")}
                    </p>

                    <p>
                        💳
                        <strong>Payment:</strong>
                        ${escapeHtml(
                            formatPaymentCommitment(
                                offer.payment_commitment
                            )
                        )}
                    </p>

                    <p>
                        📍
                        <strong>Work Location:</strong>
                        ${escapeHtml(
                            offer.job_location ||
                            "Location not specified"
                        )}
                    </p>

                    <p>
                        📌 
                        <strong>Meeting Point:</strong>
                        ${escapeHtml(
                            offer.meeting_point ||
                            "Same as work location"
                        )}
                    </p>

                    <p>
                        📅
                        <strong>Work Date:</strong>
                        ${
                            offer.work_date
                                ? formatDate(
                                    offer.work_date
                                )
                                : "Flexible"
                        }
                    </p>

                    ${
                        offer.start_time &&
                        offer.end_time
                            ? `
                                <p>
                                    🕐
                                    <strong>Working Hours:</strong>
                                    ${escapeHtml(
                                        formatTime(
                                            offer.start_time
                                        )
                                    )}
                                    -
                                    ${escapeHtml(
                                        formatTime(
                                            offer.end_time
                                        )
                                    )}
                                </p>
                            `
                            : ""
                    }

                    ${
                        offer.offer_message
                            ? `
                                <div class="job-description">
                                    <h4>
                                        Message from Employer
                                    </h4>

                                    <p>
                                        ${escapeHtml(
                                            offer.offer_message
                                        )}
                                    </p>
                                </div>
                            `
                            : ""
                    }
                </div>

                <div class="applicant-actions">
                    <button
                        class="primary-btn"
                        onclick="respondToJobOffer(
                            ${offer.offer_id},
                            'ACCEPTED'
                        )">

                        Accept Offer

                    </button>

                    <button
                        class="danger-btn"
                        onclick="respondToJobOffer(
                            ${offer.offer_id},
                            'DECLINED'
                        )">

                        Decline

                    </button>
                </div>
            `;

            container.appendChild(
                card
            );
        }
    );

}


// ============================================================
// RESPOND TO SELF JOB OFFER
// ============================================================
async function respondToJobOffer(
    offerId,
    response
){
    const email =
        localStorage.getItem(
            "email"
        );

    if(!email){
        alert(
            "Please log in again."
        );
        return;
    }

    const message =
        response === "ACCEPTED"
            ? "Accept this job offer? By accepting, you agree to the displayed wage, work date, location and payment schedule."
            : "Decline this job offer?";

    if(!confirm(message)){
        return;
    }

    try{
        const apiResponse =
            await fetch(
                `${API_BASE_URL}/respond_job_offer`,
                {
                    method:"POST",

                    headers:{
                        "Content-Type":
                            "application/json"
                    },
                    body:JSON.stringify({

                        offer_id:
                            offerId,

                        response:
                            response,

                        response_mode:
                            "SELF",

                        responder_email:
                            email
                    })
                }
            );

        const data =
            await apiResponse.json();

        if(apiResponse.ok){
            alert(
                data.message
            );
            await loadMyJobOffers();
        }
        else{
            alert(
                data.message ||
                "Unable to respond to offer."
            );
        }
    }

    catch(error){
        console.error(error);

        alert(
            "Unable to connect to server."
        );
    }
}

// ============================================================
// CLOSE JOB OFFERS
// ============================================================
function closeJobOffersModal(){
    document.getElementById(
        "jobOffersModal"
    ).style.display =
        "none";
}


// ============================================================
// LOAD ASSISTED JOB OFFERS
// ============================================================

async function loadAssistedJobOffers(){

    const email =
        localStorage.getItem(
            "email"
        );


    if(!email){

        alert(
            "Please log in again."
        );

        return;

    }


    document.getElementById(
        "assistedJobOffersModal"
    ).style.display =
        "flex";


    const container =
        document.getElementById(
            "assistedJobOffersContainer"
        );


    container.innerHTML =
        "Loading offers...";


    try{

        const response =
            await fetch(
                `${API_BASE_URL}/get_assisted_job_offers?responder_email=${encodeURIComponent(email)}`
            );


        const data =
            await response.json();


        if(
            !response.ok ||
            !data.success
        ){

            throw new Error(
                data.message ||
                "Unable to load assisted offers."
            );

        }


        renderAssistedJobOffers(
            data.offers || []
        );

    }

    catch(error){

        console.error(
            error
        );


        container.innerHTML = `
            <div class="job-error">

                <span class="material-symbols-outlined">
                    error
                </span>

                <h3>
                    Unable to load assisted offers
                </h3>

                <p>
                    ${escapeHtml(
                        error.message
                    )}
                </p>

            </div>
        `;

    }

}


// ============================================================
// RENDER ASSISTED JOB OFFERS
// ============================================================

function renderAssistedJobOffers(
    offers
){

    const container =
        document.getElementById(
            "assistedJobOffersContainer"
        );


    if(offers.length === 0){

        container.innerHTML = `
            <div class="job-empty-state">

                <span class="material-symbols-outlined">
                    task_alt
                </span>

                <h3>
                    No pending assisted offers
                </h3>

                <p>
                    Offers for beneficiaries requiring
                    assistance will appear here.
                </p>

            </div>
        `;

        return;

    }


    container.innerHTML =
        "";


    offers.forEach(
        offer => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "applicant-card";


            card.innerHTML = `

                <div class="applicant-card-header">

                    <div>

                        <h3>
                            ${escapeHtml(
                                offer.beneficiary_name
                            )}
                        </h3>

                        <p>
                            Job:
                            ${escapeHtml(
                                offer.job_title
                            )}
                        </p>

                    </div>

                    <span class="application-status">
                        Offer Pending
                    </span>

                </div>


                <div class="applicant-details">

                    <p>
                        📞
                        <strong>Beneficiary Contact:</strong>
                        ${escapeHtml(
                            offer.beneficiary_phone ||
                            "Not available"
                        )}
                    </p>

                    <p>
                        📍
                        <strong>Beneficiary Locality:</strong>
                        ${escapeHtml(
                            offer.beneficiary_location ||
                            "Not specified"
                        )}
                    </p>

                    <p>
                        🏢
                        <strong>Employer:</strong>
                        ${escapeHtml(
                            offer.employer_name ||
                            "SPARC Employer"
                        )}
                    </p>

                    <p>
                        💰
                        <strong>Wage:</strong>
                        ₹${Number(
                            offer.offered_wage
                        ).toLocaleString("en-IN")}
                    </p>

                    <p>
                        💳
                        <strong>Payment:</strong>
                        ${escapeHtml(
                            formatPaymentCommitment(
                                offer.payment_commitment
                            )
                        )}
                    </p>

                    <p>
                        📍
                        <strong>Work Location:</strong>
                        ${escapeHtml(
                            offer.job_location ||
                            "Not specified"
                        )}
                    </p>

                    <p>
                        📌
                        <strong>Meeting Point:</strong>
                        ${escapeHtml(
                            offer.meeting_point ||
                            "Same as work location"
                        )}
                    </p>

                    <p>
                        📅
                        <strong>Work Date:</strong>
                        ${
                            offer.work_date
                                ? formatDate(
                                    offer.work_date
                                )
                                : "Flexible"
                        }
                    </p>

                    ${
                        offer.offer_message
                            ? `
                                <div class="job-description">

                                    <h4>
                                        Employer Message
                                    </h4>

                                    <p>
                                        ${escapeHtml(
                                            offer.offer_message
                                        )}
                                    </p>

                                </div>
                            `
                            : ""
                    }

                </div>


                <div class="applicant-actions">

                    <button
                        class="primary-btn"
                        onclick="respondToAssistedOffer(
                            ${offer.offer_id},
                            'ACCEPTED'
                        )">

                        Beneficiary Accepted

                    </button>


                    <button
                        class="danger-btn"
                        onclick="respondToAssistedOffer(
                            ${offer.offer_id},
                            'DECLINED'
                        )">

                        Beneficiary Declined

                    </button>

                </div>

            `;


            container.appendChild(
                card
            );

        }
    );

}


// ============================================================
// RESPOND TO ASSISTED OFFER
// ============================================================

async function respondToAssistedOffer(
    offerId,
    response
){

    const email =
        localStorage.getItem(
            "email"
        );


    if(!email){

        alert(
            "Please log in again."
        );

        return;

    }


    const message =
        response === "ACCEPTED"
            ? "Confirm that the beneficiary has agreed to this job offer?"
            : "Confirm that the beneficiary has declined this job offer?";


    if(!confirm(message)){

        return;

    }


    try{

        const apiResponse =
            await fetch(
                `${API_BASE_URL}/respond_job_offer`,
                {
                    method:"POST",

                    headers:{
                        "Content-Type":
                            "application/json"
                    },

                    body:JSON.stringify({

                        offer_id:
                            offerId,

                        response:
                            response,

                        response_mode:
                            "ASSISTED",

                        responder_email:
                            email

                    })

                }
            );


        const data =
            await apiResponse.json();


        if(!apiResponse.ok){

            alert(
                data.message ||
                "Unable to record beneficiary response."
            );

            return;

        }


        alert(
            response === "ACCEPTED"
                ? "Beneficiary acceptance recorded. Job assignment created."
                : "Beneficiary decline recorded."
        );


        await loadAssistedJobOffers();

    }

    catch(error){

        console.error(
            error
        );

        alert(
            "Unable to connect to server."
        );

    }

}


// ============================================================
// CLOSE ASSISTED OFFERS
function closeAssistedJobOffersModal(){
    document.getElementById(
        "assistedJobOffersModal"
    ).style.display =
        "none";
}


// ============================================================
// LOAD JOB ASSIGNMENTS
// ============================================================

async function loadMyAssignments(){

    const email =
        localStorage.getItem(
            "email"
        );

    const role =
        localStorage.getItem(
            "role"
        );


    if(!email || !role){

        alert(
            "Please log in again."
        );

        return;

    }


    document.getElementById(
        "assignmentsModal"
    ).style.display =
        "flex";


    const container =
        document.getElementById(
            "assignmentsContainer"
        );


    container.innerHTML =
        "Loading assignments...";


    try{

        const response =
            await fetch(
                `${API_BASE_URL}/get_job_assignments?email=${encodeURIComponent(email)}&role=${encodeURIComponent(role)}`
            );


        const data =
            await response.json();


        if(
            !response.ok ||
            !data.success
        ){

            throw new Error(
                data.message ||
                "Unable to load assignments."
            );

        }


        renderAssignments(
            data.assignments || []
        );

    }

    catch(error){

        console.error(
            error
        );


        container.innerHTML = `

            <div class="job-error">

                <span class="material-symbols-outlined">
                    error
                </span>

                <h3>
                    Unable to load assignments
                </h3>

                <p>
                    ${escapeHtml(
                        error.message
                    )}
                </p>

            </div>

        `;

    }

}


// ============================================================
// RENDER ASSIGNMENTS
// ============================================================

function renderAssignments(
    assignments
){

    const container =
        document.getElementById(
            "assignmentsContainer"
        );


    if(assignments.length === 0){

        container.innerHTML = `

            <div class="job-empty-state">

                <span class="material-symbols-outlined">
                    assignment
                </span>

                <h3>
                    No job assignments
                </h3>

                <p>
                    Accepted job offers will appear here.
                </p>

            </div>

        `;

        return;

    }


    container.innerHTML =
        "";


    assignments.forEach(
        assignment => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "applicant-card";


            const role =
                localStorage.getItem(
                    "role"
                );


            let personDetails = "";


            if(role === "Employer"){

                personDetails = `

                    <p>
                        👤
                        <strong>Beneficiary:</strong>
                        ${escapeHtml(
                            assignment.beneficiary_name ||
                            "Not available"
                        )}
                    </p>

                    <p>
                        📞
                        <strong>Contact:</strong>
                        ${escapeHtml(
                            assignment.beneficiary_phone ||
                            "Not available"
                        )}
                    </p>

                    <p>
                        📍
                        <strong>Locality:</strong>
                        ${escapeHtml(
                            assignment.beneficiary_location ||
                            "Not available"
                        )}
                    </p>

                `;

            }


            else if(
                role === "Beneficiary"
            ){

                personDetails = `

                    <p>
                        🏢
                        <strong>Employer:</strong>
                        ${escapeHtml(
                            assignment.employer_name ||
                            "Employer"
                        )}
                    </p>

                    <p>
                        📧
                        <strong>Employer Contact:</strong>
                        ${escapeHtml(
                            assignment.employer_contact ||
                            "Not available"
                        )}
                    </p>

                `;

            }


            else{

                personDetails = `

                    <p>
                        👤
                        <strong>Beneficiary:</strong>
                        ${escapeHtml(
                            assignment.beneficiary_name ||
                            "Not available"
                        )}
                    </p>

                    <p>
                        🏢
                        <strong>Employer:</strong>
                        ${escapeHtml(
                            assignment.employer_name ||
                            "Not available"
                        )}
                    </p>

                `;

            }


            card.innerHTML = `

                <div class="applicant-card-header">

                    <div>

                        <h3>
                            ${escapeHtml(
                                assignment.job_title
                            )}
                        </h3>

                        <p>
                            Assignment #${assignment.assignment_id}
                        </p>

                    </div>

                    <span class="application-status">

                        ${escapeHtml(
                            assignment.status
                        )}

                    </span>

                </div>


                <div class="applicant-details">

                    ${personDetails}


                    <p>
                        📅
                        <strong>Work Date:</strong>
                        ${
                            assignment.work_date
                                ? formatDate(
                                    assignment.work_date
                                )
                                : "Not specified"
                        }
                    </p>


                    <p>
                        📍
                        <strong>Work Location:</strong>
                        ${escapeHtml(
                            assignment.work_location ||
                            "Not specified"
                        )}
                    </p>


                    <p>
                        📌
                        <strong>Meeting Point:</strong>
                        ${escapeHtml(
                            assignment.meeting_point ||
                            "Same as work location"
                        )}
                    </p>


                    <p>
                        💰
                        <strong>Agreed Wage:</strong>
                        ₹${Number(
                            assignment.agreed_wage
                        ).toLocaleString(
                            "en-IN"
                        )}
                        /
                        ${escapeHtml(
                            assignment.wage_type ||
                            "daily"
                        )}
                    </p>


                    <p>
                        💳
                        <strong>Payment:</strong>
                        ${escapeHtml(
                            formatPaymentCommitment(
                                assignment.payment_commitment
                            )
                        )}
                    </p>

                    
                    ${
                        role === "Employer"
                            ? assignment.status === "ASSIGNED"
                                ? `
                                    <div class="applicant-actions">

                                        <button
                                            class="primary-btn"
                                            onclick="startWorkSession(
                                                ${assignment.assignment_id}
                                            )">

                                            <span class="material-symbols-outlined">
                                                play_arrow
                                            </span>

                                            Start Work

                                        </button>

                                    </div>
                                `
                                : assignment.status === "IN_PROGRESS"
                                    ? `
                                        <div class="applicant-actions">

                                            <button
                                                class="primary-btn"
                                                onclick="loadWorkSessions()">

                                                <span class="material-symbols-outlined">
                                                    work_history
                                                </span>

                                                Manage Work Session

                                            </button>

                                        </div>
                                    `
                                    : assignment.status === "PAYMENT_DUE"
                                        ? `
                                            <div class="applicant-actions">

                                                <button
                                                    class="primary-btn"
                                                    onclick="loadEmployerPayments()">

                                                    <span class="material-symbols-outlined">
                                                        payments
                                                    </span>

                                                    Record Payment

                                                </button>

                                            </div>
                                        `
                                        : ""
                            : ""
                    }

                    
                    ${
                        role === "Beneficiary" &&
                        assignment.work_date === getTodayDate() &&
                        assignment.status === "ASSIGNED"
                            ? `
                                <div class="applicant-actions">

                                    <button
                                        class="secondary-btn"
                                        onclick="openAssignmentLocation(
                                            ${assignment.assignment_id}
                                        )">

                                        <span class="material-symbols-outlined">
                                            location_on
                                        </span>

                                        I'm On My Way

                                    </button>

                                </div>
                            `
                            : ""
                    }


                    <p>
                        ✅
                        <strong>Accepted:</strong>
                        ${formatDateTime(
                            assignment.accepted_at
                        )}
                    </p>

                </div>

            `;


            container.appendChild(
                card
            );

        }
    );

}


// ============================================================
// CLOSE ASSIGNMENTS MODAL
// ============================================================

function closeAssignmentsModal(){

    document.getElementById(
        "assignmentsModal"
    ).style.display =
        "none";

}

// ============================================================
// START WORK SESSION
async function startWorkSession(assignmentId) {
    const employerEmail =
        localStorage.getItem("email");

    if (!employerEmail) {
        alert("Please log in again.");
        return;
    }

    if (
        !confirm(
            "Start the work session for this assignment?"
        )
    ) {
        return;
    }

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/start_work_session`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        assignment_id:
                            assignmentId,

                        employer_email:
                            employerEmail
                    })
                }
            );

        const data =
            await response.json();

        if (!response.ok || !data.success) {
            alert(
                data.message ||
                "Unable to start work."
            );
            return;
        }

        alert(
            "Work session started successfully."
        );

        await loadMyAssignments();

        await loadWorkSessions();
    }

    catch (error) {
        console.error(
            "Start work error:",
            error
        );

        alert(
            "Unable to connect to server."
        );
    }
}

// ============================================================
// CALCULATE WAGE
// ============================================================
async function calculateWage(
    sessionId
){
    const employerEmail =
        localStorage.getItem(
            "email"
        );

    if(!employerEmail){
        alert(
            "Please log in again."
        );
        return;
    }

    if(
        !confirm(
            "Calculate the wage for this completed work session?"
        )
    ){
        return;
    }

    try{
        const response =
            await fetch(
                `${API_BASE_URL}/calculate_wage`,
                {
                    method:"POST",

                    headers:{
                        "Content-Type":
                            "application/json"
                    },

                    body:JSON.stringify({
                        session_id:
                            sessionId,

                        employer_email:
                            employerEmail
                    })
                }
            );

        const data =
            await response.json();

        if(!response.ok){
            alert(
                data.message ||
                "Unable to calculate wage."
            );
            return;
        }

        alert(
            `Wage calculated: ₹${Number(
                data.wage_earned
            ).toLocaleString("en-IN")}`
        );

        await loadWorkSessions();

        await loadMyAssignments();
    }

    catch(error){
        console.error(
            error
        );

        alert(
            "Unable to connect to server."
        );
    }
}


// ============================================================
// RECORD PAYMENT
// ============================================================
async function recordPayment(
    wageId
){
    const employerEmail =
        localStorage.getItem(
            "email"
        );

    if(!employerEmail){
        alert(
            "Please log in again."
        );
        return;
    }

    const paymentMethod =
        prompt(
            "Enter payment method (UPI, Cash, Bank Transfer, etc.):"
        );

    if(!paymentMethod){
        return;
    }

    const reference =
        prompt(
            "Enter transaction/reference number if available:"
        );

    if(
        !confirm(
            "Confirm that you have paid the beneficiary the full wage amount?"
        )
    ){
        return;
    }

    try{
        const response =
            await fetch(
                `${API_BASE_URL}/record_payment`,
                {
                    method:"POST",

                    headers:{
                        "Content-Type":
                            "application/json"
                    },

                    body:JSON.stringify({
                        wage_id:
                            wageId,

                        employer_email:
                            employerEmail,

                        payment_method:
                            paymentMethod,

                        transaction_reference:
                            reference
                    })
                }
            );

        const data =
            await response.json();

        if(!response.ok){
            alert(
                data.message ||
                "Unable to record payment."
            );
            return;
        }

        alert(
            `Payment recorded: ₹${Number(
                data.amount
            ).toLocaleString("en-IN")}`
        );

        await loadMyAssignments();

        await loadWorkSessions();
    }

    catch(error){
        console.error(
            error
        );

        alert(
            "Unable to connect to server."
        );
    }
}


// ============================================================
// LOAD PAYMENTS
// ============================================================
async function loadMyPayments(){
    const email =
        localStorage.getItem(
            "email"
        );

    const role =
        localStorage.getItem(
            "role"
        );

    if(!email || !role){
        alert(
            "Please log in again."
        );
        return;
    }

    document.getElementById(
        "paymentsModal"
    ).style.display =
        "flex";

    const container =
        document.getElementById(
            "paymentsContainer"
        );

    container.innerHTML =
        "Loading payments...";
    try{
        const response =
            await fetch(
                `${API_BASE_URL}/get_payments?email=${encodeURIComponent(email)}&role=${encodeURIComponent(role)}`
            );

        const data =
            await response.json();

        if(
            !response.ok ||
            !data.success
        ){
            throw new Error(
                data.message ||
                "Unable to load payments."
            );
        }

        renderPayments(
            data.payments || []
        );
    }

    catch(error){
        console.error(
            error
        );

        container.innerHTML = `
            <div class="job-error">
                <h3>
                    Unable to load payments
                </h3>

                <p>
                    ${escapeHtml(
                        error.message
                    )}
                </p>
            </div>
        `;
    }
}


// ============================================================
// RENDER PAYMENTS
// ============================================================
function renderPayments(
    payments
){
    const container =
        document.getElementById(
            "paymentsContainer"
        );
    if(payments.length === 0){
        container.innerHTML = `

            <div class="job-empty-state">
                <span class="material-symbols-outlined">
                    payments
                </span>

                <h3>
                    No payment records
                </h3>

                <p>
                    Completed work payments will appear here.
                </p>
            </div>
        `;
        return;
    }

    container.innerHTML =
        "";

    payments.forEach(
        payment => {
            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "applicant-card";

            const canConfirm =
                localStorage.getItem(
                    "role"
                ) === "Beneficiary" &&
                payment.payment_status === "PAID" &&
                payment.beneficiary_confirmation !== "CONFIRMED";

            card.innerHTML = `

                <div class="applicant-card-header">
                    <div>
                        <h3>
                            ${escapeHtml(
                                payment.job_title
                            )}
                        </h3>

                        ${
                            payment.employer_name
                                ? `
                                    <p>
                                        Employer:
                                        ${escapeHtml(
                                            payment.employer_name
                                        )}
                                    </p>
                                `
                                : ""
                        }
                    </div>
                
                    <span class="application-status">
                        ${escapeHtml(
                            payment.payment_status
                        )}
                    </span>
                </div>

                <div class="applicant-details">
                    <p>
                        📅
                        <strong>Work Date:</strong>
                        ${
                            payment.work_date
                                ? formatDate(
                                    payment.work_date
                                )
                                : "Not specified"
                        }
                    </p>

                    <p>
                        💰
                        <strong>Amount:</strong>
                        ₹${Number(
                            payment.amount
                        ).toLocaleString(
                            "en-IN"
                        )}
                    </p>

                    <p>
                        💳
                        <strong>Payment Method:</strong>
                        ${escapeHtml(
                            payment.payment_method ||
                            "Not specified"
                        )}
                    </p>

                    ${
                        payment.transaction_reference
                            ? `
                                <p>
                                    🔖
                                    <strong>Reference:</strong>
                                    ${escapeHtml(
                                        payment.transaction_reference
                                    )}
                                </p>
                            `
                            : ""
                    }

                    <p>
                        🏢
                        <strong>Employer Confirmation:</strong>
                        ${escapeHtml(
                            payment.employer_confirmation
                        )}
                    </p>

                    <p>
                        👤
                        <strong>Your Confirmation:</strong>
                        ${escapeHtml(
                            payment.beneficiary_confirmation
                        )}
                    </p>
                </div>

                ${
                    canConfirm
                        ? `
                            <div class="applicant-actions">

                                <button
                                    class="primary-btn"
                                    onclick="confirmPaymentReceived(
                                        ${payment.payment_id}
                                    )">

                                    I Received This Payment

                                </button>


                                <button
                                    class="secondary-btn"
                                    onclick="reportPaymentDispute(
                                        ${payment.payment_id}
                                    )">

                                    I Did Not Receive This Payment

                                </button>

                            </div>
                        `
                        : ""
                }
            `;

            container.appendChild(
                card
            );
        }
    );
}


// ============================================================
// CONFIRM PAYMENT RECEIVED
// ============================================================
async function confirmPaymentReceived(
    paymentId
){
    const email =
        localStorage.getItem(
            "email"
        );

    if(!email){
        alert(
            "Please log in again."
        );
        return;
    }

    if(
        !confirm(
            "Confirm that you received the full payment shown for this work?"
        )
    ){
        return;
    }

    try{
        const response =
            await fetch(
                `${API_BASE_URL}/confirm_payment_received`,
                {
                    method:"POST",

                    headers:{
                        "Content-Type":
                            "application/json"
                    },

                    body:JSON.stringify({
                        payment_id:
                            paymentId,

                        confirmation_mode:
                            "SELF",

                        responder_email:
                            email
                    })
                }
            );

        const data =
            await response.json();

        if(!response.ok){
            alert(
                data.message ||
                "Unable to confirm payment."
            );
            return;
        }

        alert(
            "Payment received confirmation recorded."
        );

        await loadMyPayments();
    }

    catch(error){
        console.error(
            error
        );

        alert(
            "Unable to connect to server."
        );
    }
}


// ============================================================
// LOAD ADMIN EMPLOYMENT OVERVIEW
// ============================================================
async function loadAdminEmploymentOverview(){
    const email =
        localStorage.getItem(
            "email"
        );

    if(!email){
        alert(
            "Please log in again."
        );
        return;
    }

    document.getElementById(
        "adminEmploymentModal"
    ).style.display =
        "flex";

    document.getElementById(
        "employmentRecordsContainer"
    ).innerHTML =
        "Loading employment records...";

    try{
        const response =
            await fetch(
                `${API_BASE_URL}/admin/employment_overview?email=${encodeURIComponent(email)}`
            );

        const data =
            await response.json();

        if(
            !response.ok ||
            !data.success
        ){
            throw new Error(
                data.message ||
                "Unable to load employment overview."
            );
        }

        renderEmploymentOverview(
            data.overview
        );

        renderEmploymentRecords(
            data.records || []
        );
    }

    catch(error){
        console.error(
            error
        );

        document.getElementById(
            "employmentRecordsContainer"
        ).innerHTML = `

            <div class="job-error">
                <h3>
                    Unable to load employment monitoring
                </h3>

                <p>
                    ${escapeHtml(
                        error.message
                    )}
                </p>
            </div>
        `;
    }
}


// ============================================================
// RENDER EMPLOYMENT OVERVIEW
// ============================================================
function renderEmploymentOverview(
    overview
){
    const container =
        document.getElementById(
            "employmentOverviewCards"
        );

    container.innerHTML = `
        <div class="stat-card">
            <h3>
                ${Number(
                    overview.total_assignments || 0
                )}
            </h3>

            <p>
                Total Assignments
            </p>
        </div>

        <div class="stat-card">
            <h3>
                ${Number(
                    overview.in_progress || 0
                )}
            </h3>

            <p>
                In Progress
            </p>
        </div>

        <div class="stat-card">
            <h3>
                ${Number(
                    overview.work_completed || 0
                )}
            </h3>

            <p>
                Work Completed
            </p>
        </div>

        <div class="stat-card">
            <h3>
                ${Number(
                    overview.payment_due || 0
                )}
            </h3>

            <p>
                Payment Due
            </p>
        </div>

        <div class="stat-card">
            <h3>
                ${Number(
                    overview.paid || 0
                )}
            </h3>

            <p>
                Paid
            </p>
        </div>

        <div class="stat-card">
            <h3>
                ${Number(
                    overview.payment_verified || 0
                )}
            </h3>

            <p>
                Payment Verified
            </p>
        </div>
    `;
}


// ============================================================
// RENDER EMPLOYMENT RECORDS
// ============================================================
function renderEmploymentRecords(
    records
){
    const container =
        document.getElementById(
            "employmentRecordsContainer"
        );

    if(records.length === 0){
        container.innerHTML = `
            <div class="job-empty-state">
                <span class="material-symbols-outlined">
                    work_off
                </span>

                <h3>
                    No employment records
                </h3>

                <p>
                    Accepted job assignments will appear here.
                </p>
            </div>
        `;
        return;
    }

    container.innerHTML =
        "";

    records.forEach(
        record => {
            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "applicant-card";

            let paymentClass =
                "application-status";

            if(
                record.payment_status ===
                "VERIFIED"
            ){
                paymentClass +=
                    " status-success";
            }

            else if(
                record.payment_status ===
                "PAID"
            ){
                paymentClass +=
                    " status-warning";
            }

            else if(
                record.wage_status ===
                "DUE"
            ){
                paymentClass +=
                    " status-danger";
            }

            card.innerHTML = `

                <div class="applicant-card-header">
                    <div>
                        <h3>
                            ${escapeHtml(
                                record.job_title
                            )}
                        </h3>

                        <p>
                            Assignment #${record.assignment_id}
                        </p>
                    </div>

                    <span class="${paymentClass}">
                        ${escapeHtml(
                            record.assignment_status
                        )}
                    </span>
                </div>

                <div class="applicant-details">
                    <p>
                        👤
                        <strong>Beneficiary:</strong>
                        ${escapeHtml(
                            record.beneficiary_name
                        )}
                    </p>

                    <p>
                        📞
                        <strong>Contact:</strong>
                        ${escapeHtml(
                            record.beneficiary_phone ||
                            "Not available"
                        )}
                    </p>

                    <p>
                        📍
                        <strong>Beneficiary Locality:</strong>
                        ${escapeHtml(
                            record.beneficiary_location ||
                            "Not specified"
                        )}
                    </p>

                    <p>
                        🏢
                        <strong>Employer:</strong>
                        ${escapeHtml(
                            record.employer_name ||
                            "Not available"
                        )}
                    </p>

                    <p>
                        📧
                        <strong>Employer Email:</strong>
                        ${escapeHtml(
                            record.employer_email
                        )}
                    </p>

                    <p>
                        📅
                        <strong>Work Date:</strong>
                        ${
                            record.work_date
                                ? formatDate(
                                    record.work_date
                                )
                                : "Not specified"
                        }
                    </p>

                    <p>
                        📍
                        <strong>Work Location:</strong>
                        ${escapeHtml(
                            record.work_location ||
                            "Not specified"
                        )}
                    </p>

                    <p>
                        📌
                        <strong>Meeting Point:</strong>
                        ${escapeHtml(
                            record.meeting_point ||
                            "Not specified"
                        )}
                    </p>

                    <p>
                        💰
                        <strong>Agreed Wage:</strong>
                        ₹${Number(
                            record.agreed_wage || 0
                        ).toLocaleString(
                            "en-IN"
                        )}
                        /
                        ${escapeHtml(
                            record.wage_type ||
                            "daily"
                        )}
                    </p>

                    <p>
                        💳
                        <strong>Payment Commitment:</strong>
                        ${escapeHtml(
                            formatPaymentCommitment(
                                record.payment_commitment
                            )
                        )}
                    </p>

                    ${
                        record.work_session_id
                            ? `
                                <hr>

                                <p>
                                    🕐
                                    <strong>Work Status:</strong>
                                    ${escapeHtml(
                                        record.work_status ||
                                        "Not started"
                                    )}
                                </p>

                                ${
                                    record.hours_worked !== null &&
                                    record.hours_worked !== undefined
                                        ? `
                                            <p>
                                                ⏱
                                                <strong>Hours Worked:</strong>
                                                ${escapeHtml(
                                                    String(
                                                        record.hours_worked
                                                    )
                                                )}
                                            </p>
                                        `
                                        : ""
                                }
                            `
                            : `
                                <p>
                                    🕐
                                    <strong>Work Session:</strong>
                                    Not started
                                </p>
                            `
                    }

                    ${
                        record.wage_id
                            ? `
                                <hr>

                                <p>
                                    💵
                                    <strong>Wage Earned:</strong>
                                    ₹${Number(
                                        record.wage_earned || 0
                                    ).toLocaleString(
                                        "en-IN"
                                    )}
                                </p>

                                <p>
                                    <strong>Wage Status:</strong>
                                    ${escapeHtml(
                                        record.wage_status ||
                                        "Unknown"
                                    )}
                                </p>
                            `
                            : ""
                    }

                    ${
                        record.payment_id
                            ? `
                                <hr>

                                <p>
                                    💳
                                    <strong>Payment Status:</strong>
                                    ${escapeHtml(
                                        record.payment_status ||
                                        "Unknown"
                                    )}
                                </p>

                                <p>
                                    <strong>Beneficiary Confirmation:</strong>
                                    ${escapeHtml(
                                        record.beneficiary_confirmation ||
                                        "PENDING"
                                    )}
                                </p>

                                ${
                                    record.payment_date
                                        ? `
                                            <p>
                                                📅
                                                <strong>Paid On:</strong>
                                                ${formatDateTime(
                                                    record.payment_date
                                                )}
                                            </p>
                                        `
                                        : ""
                                }
                            `
                            : ""
                    }
                </div>
            `;

            container.appendChild(
                card
            );
        }
    );
}


// ============================================================
// CLOSE ADMIN EMPLOYMENT MODAL
// ============================================================
function closeAdminEmploymentModal(){
    document.getElementById(
        "adminEmploymentModal"
    ).style.display =
        "none";
}


// ============================================================
// REPORT PAYMENT DISPUTE
// ============================================================
async function reportPaymentDispute(
    paymentId
){
    const email =
        localStorage.getItem(
            "email"
        );

    const role =
        localStorage.getItem(
            "role"
        );

    if(!email || !role){
        alert(
            "Please log in again."
        );
        return;
    }

    const reason =
        prompt(
            "Please explain why you did not receive this payment:"
        );

    if(!reason || !reason.trim()){
        return;
    }

    if(
        !confirm(
            "Submit this payment dispute to SPARC Admin?"
        )
    ){

        return;
    }

    try{
        const response =
            await fetch(
                `${API_BASE_URL}/report_payment_dispute`,
                {
                    method:"POST",

                    headers:{
                        "Content-Type":
                            "application/json"
                    },

                    body:JSON.stringify({
                        payment_id:
                            paymentId,

                        reported_by_email:
                            email,

                        reported_by_role:
                            role,

                        dispute_reason:
                            reason.trim()
                    })
                }
            );

        const data =
            await response.json();

        if(!response.ok){
            alert(
                data.message ||
                "Unable to report dispute."
            );
            return;
        }

        alert(
            "Payment dispute has been reported to SPARC Admin."
        );

        await loadMyPayments();
    }

    catch(error){
        console.error(
            error
        );
        alert(
            "Unable to connect to server."
        );
    }
}


// ============================================================
// LOAD ASSISTED PAYMENTS
// ============================================================
async function loadAssistedPayments(){
    const email =
        localStorage.getItem(
            "email"
        );

    const role =
        localStorage.getItem(
            "role"
        );

    if(!email || !role){
        alert(
            "Please log in again."
        );
        return;
    }

    document.getElementById(
        "assistedPaymentsModal"
    ).style.display =
        "flex";

    const container =
        document.getElementById(
            "assistedPaymentsContainer"
        );

    container.innerHTML =
        "Loading payments...";

    try{
        const response =
            await fetch(
                `${API_BASE_URL}/get_payments?email=${encodeURIComponent(email)}`
            );

        const responseText =
            await response.text();

        let data;

        try {
            data =
                JSON.parse(responseText);
        }
        catch(error) {
            throw new Error(
                `Server returned HTTP ${response.status} instead of JSON.`
            );
        }

        if(
            !response.ok ||
            !data.success
        ){
            throw new Error(
                data.message ||
                "Unable to load payments."
            );
        }

        const payments =
            (data.payments || [])
            .filter(
                payment =>
                    payment.payment_status === "PAID" &&
                    payment.beneficiary_confirmation !== "CONFIRMED"
            );

        renderAssistedPayments(
            payments
        );
    }

    catch(error){
        console.error(
            error
        );

        container.innerHTML = `
            <div class="job-error">
                <h3>
                    Unable to load assisted payments
                </h3>

                <p>
                    ${escapeHtml(
                        error.message
                    )}
                </p>
            </div>
        `;
    }
}


// ============================================================
// RENDER ASSISTED PAYMENTS
// ============================================================
function renderAssistedPayments(
    payments
){
    const container =
        document.getElementById(
            "assistedPaymentsContainer"
        );

    if(payments.length === 0){
        container.innerHTML = `
            <div class="job-empty-state">
                <span class="material-symbols-outlined">
                    task_alt
                </span>

                <h3>
                    No pending confirmations
                </h3>

                <p>
                    There are no assisted payments waiting for confirmation.
                </p>
            </div>
        `;
        return;
    }

    container.innerHTML =
        "";

    payments.forEach(
        payment => {
            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "applicant-card";

            card.innerHTML = `
                <div class="applicant-card-header">
                    <div>
                        <h3>
                            ${escapeHtml(
                                payment.job_title
                            )}
                        </h3>

                        <p>
                            Payment #${payment.payment_id}
                        </p>
                    </div>

                    <span class="application-status">
                        PAID — CONFIRMATION PENDING
                    </span>
                </div>

                <div class="applicant-details">
                    <p>
                        👤
                        <strong>Beneficiary:</strong>
                        ${escapeHtml(
                            payment.beneficiary_name ||
                            "Not available"
                        )}
                    </p>

                    <p>
                        📞
                        <strong>Contact:</strong>
                        ${escapeHtml(
                            payment.beneficiary_phone ||
                            "Not available"
                        )}
                    </p>

                    <p>
                        📍
                        <strong>Locality:</strong>
                        ${escapeHtml(
                            payment.beneficiary_location ||
                            "Not specified"
                        )}
                    </p>

                    <p>
                        🏢
                        <strong>Employer:</strong>
                        ${escapeHtml(
                            payment.employer_name ||
                            "Not available"
                        )}
                    </p>

                    <p>
                        📅
                        <strong>Work Date:</strong>
                        ${
                            payment.work_date
                                ? formatDate(
                                    payment.work_date
                                )
                                : "Not specified"
                        }
                    </p>

                    <p>
                        💰
                        <strong>Amount:</strong>
                        ₹${Number(
                            payment.amount
                        ).toLocaleString(
                            "en-IN"
                        )}
                    </p>

                    <p>
                        💳
                        <strong>Payment Method:</strong>
                        ${escapeHtml(
                            payment.payment_method ||
                            "Not specified"
                        )}
                    </p>
                </div>

                <div class="applicant-actions">
                    <button
                        class="primary-btn"
                        onclick="confirmAssistedPayment(
                            ${payment.payment_id}
                        )">

                        Beneficiary Confirmed Payment
                    </button>

                    <button
                        class="secondary-btn"
                        onclick="reportAssistedPaymentDispute(
                            ${payment.payment_id}
                        )">

                        Beneficiary Did Not Receive
                    </button>
                </div>
            `;

            container.appendChild(
                card
            );
        }
    );
}


// ============================================================
// CONFIRM ASSISTED PAYMENT
// ============================================================
async function confirmAssistedPayment(
    paymentId
){
    const responderEmail =
        localStorage.getItem(
            "email"
        );

    if(!responderEmail){
        alert(
            "Please log in again."
        );
        return;
    }

    if(
        !confirm(
            "Have you personally communicated with the beneficiary and confirmed that they received the full payment?"
        )
    ){
        return;
    }

    try{
        const response =
            await fetch(
                `${API_BASE_URL}/confirm_payment_received`,
                {
                    method:"POST",

                    headers:{
                        "Content-Type":
                            "application/json"
                    },

                    body:JSON.stringify({
                        payment_id:
                            paymentId,

                        confirmation_mode:
                            "ASSISTED",

                        responder_email:
                            responderEmail
                    })
                }
            );

        const data =
            await response.json();

        if(!response.ok){
            alert(
                data.message ||
                "Unable to confirm payment."
            );
            return;
        }

        alert(
            "Assisted payment confirmation recorded."
        );

        await loadAssistedPayments();
    }

    catch(error){
        console.error(
            error
        );

        alert(
            "Unable to connect to server."
        );
    }
}


// ============================================================
// REPORT ASSISTED PAYMENT DISPUTE
// ============================================================
async function reportAssistedPaymentDispute(
    paymentId
){
    const email =
        localStorage.getItem(
            "email"
        );

    const role =
        localStorage.getItem(
            "role"
        );

    if(!email || !role){
        alert(
            "Please log in again."
        );
        return;
    }

    const reason =
        prompt(
            "Enter the beneficiary's reported payment issue:"
        );

    if(!reason || !reason.trim()){
        return;
    }

    if(
        !confirm(
            "Submit this payment issue to SPARC Admin?"
        )
    ){
        return;
    }

    try{
        const response =
            await fetch(
                `${API_BASE_URL}/report_payment_dispute`,
                {
                    method:"POST",

                    headers:{
                        "Content-Type":
                            "application/json"
                    },

                    body:JSON.stringify({
                        payment_id:
                            paymentId,

                        reported_by_email:
                            email,

                        reported_by_role:
                            role,

                        dispute_reason:
                            reason.trim()
                    })
                }
            );

        const data =
            await response.json();

        if(!response.ok){
            alert(
                data.message ||
                "Unable to report payment issue."
            );
            return;
        }

        alert(
            "Payment issue has been reported to Admin."
        );

        await loadAssistedPayments();
    }

    catch(error){
        console.error(
            error
        );

        alert(
            "Unable to connect to server."
        );
    }
}


// ============================================================
// LOCATION SHARING STATE
// ============================================================
let activeLocationSessionId = null;

let locationWatchId = null;

let selectedLocationAssignmentId = null;

let selectedLocationPurpose = null;


// ============================================================
// START BENEFICIARY LOCATION
// ============================================================
function startBeneficiaryLocation(){
    const role =
        localStorage.getItem("role");

    if(role !== "Beneficiary"){
        alert(
            "Only beneficiaries can use this option."
        );
        return;
    }

    selectedLocationPurpose =
        "GOING_TO_WORK";

    selectedLocationAssignmentId =
        window.currentAssignmentId || null;

    if(!selectedLocationAssignmentId){
        alert(
            "Please open your job assignment first."
        );
        return;
    }

    document.getElementById(
        "locationSharingModal"
    ).style.display = "flex";

    document.getElementById(
        "locationSharingMessage"
    ).textContent =
        "Your location will be shared only while you are travelling to your assigned work location.";

    document.getElementById(
        "locationStatus"
    ).textContent =
        "Location sharing is not active.";
}


// ============================================================
// START ASSISTANCE LOCATION
// ============================================================
function startAssistanceLocation(){
    const role =
        localStorage.getItem("role");

    if(
        role !== "Volunteer" &&
        role !== "NGO"
    ){
        alert(
            "Only Volunteer or NGO users can use this option."
        );
        return;
    }

    selectedLocationPurpose =
        "ASSISTED_VISIT";

    selectedLocationAssignmentId =
        window.currentAssignmentId || null;

    document.getElementById(
        "locationSharingModal"
    ).style.display = "flex";

    document.getElementById(
        "locationSharingMessage"
    ).textContent =
        "Your location will be shared only while you are assisting the beneficiary.";
}


// ============================================================
// BEGIN LOCATION SHARING
// ============================================================
async function beginLocationSharing(){
    const email =
        localStorage.getItem("email");

    const role =
        localStorage.getItem("role");

    if(!email || !role){
        alert(
            "Please log in again."
        );
        return;
    }

    if(!navigator.geolocation){
        alert(
            "Location services are not supported by this browser."
        );
        return;
    }

    document.getElementById(
        "locationStatus"
    ).textContent =
        "Requesting location permission...";

    try{
        const response =
            await fetch(
                `${API_BASE_URL}/start_location_session`,
                {
                    method:"POST",

                    headers:{
                        "Content-Type":
                            "application/json"
                    },

                    body:JSON.stringify({
                        email:email,

                        role:role,

                        assignment_id:
                            selectedLocationAssignmentId,

                        purpose:
                            selectedLocationPurpose
                    })
                }
            );

        const data =
            await response.json();

        if(
            !response.ok ||
            !data.success
        ){
            throw new Error(
                data.message ||
                "Unable to start location session."
            );
        }

        activeLocationSessionId =
            data.session_id;

        document.getElementById(
            "locationStatus"
        ).textContent =
            "Location sharing is ACTIVE.";

        document.getElementById(
            "startLocationButton"
        ).style.display =
            "none";

        document.getElementById(
            "stopLocationButton"
        ).style.display =
            "inline-flex";

        startLocationWatcher();
    }

    catch(error){
        console.error(
            error
        );

        document.getElementById(
            "locationStatus"
        ).textContent =
            "Unable to start location sharing.";

        alert(
            error.message
        );
    }
}


// ============================================================
// WATCH USER LOCATION
// ============================================================
function startLocationWatcher(){
    if(locationWatchId !== null){
        navigator.geolocation.clearWatch(
            locationWatchId
        );
    }

    locationWatchId =
        navigator.geolocation.watchPosition(
            position => {
                updateCurrentLocation(
                    position
                );
            },

            error => {
                console.error(
                    "Location error:",
                    error
                );

                document.getElementById(
                    "locationStatus"
                ).textContent =
                    "Unable to obtain current location.";
            },

            {
                enableHighAccuracy:true,
                maximumAge:10000,
                timeout:15000
            }
        );
}


// ============================================================
// UPDATE CURRENT LOCATION
// ============================================================
async function updateCurrentLocation(
    position
){
    if(!activeLocationSessionId){
        return;
    }

    const email =
        localStorage.getItem("email");

    if(!email){
        return;
    }

    const latitude =
        position.coords.latitude;

    const longitude =
        position.coords.longitude;

    const accuracy =
        position.coords.accuracy;

    try{
        const response =
            await fetch(
                `${API_BASE_URL}/update_location`,
                {
                    method:"POST",

                    headers:{
                        "Content-Type":
                            "application/json"
                    },

                    body:JSON.stringify({
                        session_id:
                            activeLocationSessionId,

                        email:email,

                        latitude:
                            latitude,

                        longitude:
                            longitude,

                        accuracy:
                            accuracy
                    })
                }
            );

        const data =
            await response.json();

        if(!response.ok){
            console.error(
                data.message ||
                "Location update failed."
            );
            return;
        }

        document.getElementById(
            "locationStatus"
        ).textContent =
            `Location sharing is ACTIVE. Accuracy: ${Math.round(accuracy)} m`;
    }

    catch(error){
        console.error(
            "Location update error:",
            error
        );
    }
}


// ============================================================
// STOP LOCATION SHARING
// ============================================================
async function stopLocationSharing(){
    const email =
        localStorage.getItem("email");

    if(!email){
        return;
    }

    if(!activeLocationSessionId){
        closeLocationSharingModal();
        return;
    }

    try{
        const response =
            await fetch(
                `${API_BASE_URL}/stop_location_session`,
                {
                    method:"POST",

                    headers:{
                        "Content-Type":
                            "application/json"
                    },

                    body:JSON.stringify({
                        session_id:
                            activeLocationSessionId,

                        email:email
                    })
                }
            );

        const data =
            await response.json();

        if(!response.ok){
            alert(
                data.message ||
                "Unable to stop location sharing."
            );
            return;
        }

        if(locationWatchId !== null){
            navigator.geolocation.clearWatch(
                locationWatchId
            );

            locationWatchId =
                null;
        }

        activeLocationSessionId =
            null;

        document.getElementById(
            "locationStatus"
        ).textContent =
            "Location sharing has stopped.";

        document.getElementById(
            "startLocationButton"
        ).style.display =
            "inline-flex";

        document.getElementById(
            "stopLocationButton"
        ).style.display =
            "none";
    }

    catch(error){
        console.error(
            error
        );

        alert(
            "Unable to connect to server."
        );
    }
}


// ============================================================
// CLOSE LOCATION MODAL
// ============================================================
function closeLocationSharingModal(){
    document.getElementById(
        "locationSharingModal"
    ).style.display =
        "none";
}


// ============================================================
// OPEN ASSIGNMENT LOCATION
// ============================================================
function openAssignmentLocation(
    assignmentId
){
    window.currentAssignmentId =
        assignmentId;

    startBeneficiaryLocation();
}


// ============================================================
// TODAY'S DATE
// ============================================================
function getTodayDate(){
    const today =
        new Date();

    const year =
        today.getFullYear();

    const month =
        String(
            today.getMonth() + 1
        ).padStart(2, "0");

    const day =
        String(
            today.getDate()
        ).padStart(2, "0");

    return `${year}-${month}-${day}`;
}


// ============================================================
// LOAD ADMIN ACTIVE LOCATIONS
// ============================================================
async function loadActiveLocations(){
    const email =
        localStorage.getItem("email");

    const role =
        localStorage.getItem("role");

    if(!email || role !== "Admin"){
        alert(
            "Admin access required."
        );
        return;
    }

    document.getElementById(
        "activeLocationsModal"
    ).style.display = "flex";

    const container =
        document.getElementById(
            "activeLocationsContainer"
        );

    container.innerHTML =
        "Loading active locations...";

    try{
        const response =
            await fetch(
                `${API_BASE_URL}/admin/active_locations?email=${encodeURIComponent(email)}`
            );

        const data =
            await response.json();

        if(
            !response.ok ||
            !data.success
        ){
            throw new Error(
                data.message ||
                "Unable to load active locations."
            );
        }

        renderActiveLocations(
            data.locations || []
        );
    }

    catch(error){
        console.error(
            error
        );

        container.innerHTML = `
            <div class="job-error">
                <h3>
                    Unable to load active locations
                </h3>

                <p>
                    ${escapeHtml(
                        error.message
                    )}
                </p>
            </div>
        `;
    }
}


// ============================================================
// RENDER ACTIVE LOCATIONS
// ============================================================
function renderActiveLocations(
    locations
){
    const container =
        document.getElementById(
            "activeLocationsContainer"
        );

    if(locations.length === 0){
        container.innerHTML = `
            <div class="job-empty-state">
                <span class="material-symbols-outlined">
                    location_off
                </span>

                <h3>
                    No Active Location Sessions
                </h3>

                <p>
                    No user is currently sharing their location.
                </p>
            </div>
        `;
        return;
    }

    container.innerHTML = "";

    locations.forEach(
        location => {
            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "applicant-card";

            const hasCoordinates =
                location.latitude !== null &&
                location.longitude !== null;

            card.innerHTML = `
                <div class="applicant-card-header">
                    <div>
                        <h3>
                            ${
                                location.beneficiary_name
                                    ? escapeHtml(
                                        location.beneficiary_name
                                    )
                                    : escapeHtml(
                                        location.user_email
                                    )
                            }
                        </h3>

                        <p>
                            ${escapeHtml(
                                location.user_role
                            )}
                        </p>
                    </div>

                    <span class="application-status">
                        ACTIVE
                    </span>
                </div>

                <div class="applicant-details">
                    <p>
                        🎯
                        <strong>Purpose:</strong>

                        ${escapeHtml(
                            formatLocationPurpose(
                                location.purpose
                            )
                        )}
                    </p>

                    ${
                        location.job_title
                            ? `
                                <p>
                                    💼
                                    <strong>Job:</strong>

                                    ${escapeHtml(
                                        location.job_title
                                    )}
                                </p>
                            `
                            : ""
                    }

                    ${
                        location.assignment_id
                            ? `
                                <p>
                                    📋
                                    <strong>Assignment:</strong>

                                    #${location.assignment_id}
                                </p>
                            `
                            : ""
                    }

                    ${
                        hasCoordinates
                            ? `
                                <p>
                                    📍
                                    <strong>Latitude:</strong>

                                    ${Number(
                                        location.latitude
                                    ).toFixed(6)}
                                </p>

                                <p>
                                    📍
                                    <strong>Longitude:</strong>

                                    ${Number(
                                        location.longitude
                                    ).toFixed(6)}
                                </p>

                                ${
                                    location.accuracy !== null
                                        ? `
                                            <p>
                                                🎯
                                                <strong>Accuracy:</strong>

                                                ${Math.round(
                                                    location.accuracy
                                                )} m
                                            </p>
                                        `
                                        : ""
                                }

                                <div
                                    class="applicant-actions">

                                    <button
                                        class="secondary-btn"
                                        onclick="openLocationOnMap(
                                            ${Number(
                                                location.latitude
                                            )},
                                            ${Number(
                                                location.longitude
                                            )}
                                        )">

                                        <span class="material-symbols-outlined">
                                            map
                                        </span>

                                        Open Map

                                    </button>
                                </div>
                            `
                            : `
                                <p>
                                    ⏳
                                    <strong>Location:</strong>

                                    Waiting for first GPS update
                                </p>
                            `
                    }

                    <p>
                        🕐
                        <strong>Started:</strong>

                        ${formatDateTime(
                            location.started_at
                        )}
                    </p>

                    <p>
                        🔄
                        <strong>Last Updated:</strong>

                        ${formatDateTime(
                            location.last_updated_at
                        )}
                    </p>
                </div>
            `;

            container.appendChild(
                card
            );
        }
    );
}


// ============================================================
// FORMAT LOCATION PURPOSE
// ============================================================
function formatLocationPurpose(
    purpose
){
    switch(purpose){
        case "GOING_TO_WORK":
            return "Going to Work";

        case "ASSISTED_VISIT":
            return "Assisted Visit";

        default:
            return purpose || "Location Sharing";
    }
}


// ============================================================
// OPEN LOCATION ON MAP
// ============================================================
function openLocationOnMap(
    latitude,
    longitude
){
    const mapUrl =
        `https://www.google.com/maps?q=${latitude},${longitude}`;

    window.open(
        mapUrl,
        "_blank",
        "noopener,noreferrer"
    );
}


// ============================================================
// LOAD WORK SESSIONS
async function loadWorkSessions() {
    const email =
        localStorage.getItem("email");

    const role =
        localStorage.getItem("role");

    if (!email || !role) {
        return;
    }

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/get_work_sessions?email=${encodeURIComponent(email)}&role=${encodeURIComponent(role)}`
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            !data.success
        ) {

            console.error(
                data.message ||
                "Unable to load work sessions."
            );
            return;
        }

        renderWorkSessions(
            data.sessions || []
        );
    }

    catch (error) {
        console.error(
            "Work session loading error:",
            error
        );
    }
}


// ============================================================
// RENDER WORK SESSIONS
function renderWorkSessions(sessions) {
    const container =
        document.getElementById(
            "workSessionDetails"
        );

    if (!container) {
        return;
    }

    if (sessions.length === 0) {
        container.innerHTML = `
            <div class="job-empty-state">
                <span class="material-symbols-outlined">
                    work_history
                </span>

                <h3>
                    No Work Sessions
                </h3>

                <p>
                    Work sessions will appear here after work starts.
                </p>
            </div>
        `;
        return;
    }

    container.innerHTML = "";

    sessions.forEach(
        session => {
            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "applicant-card";

            let actionHTML = "";

            // ------------------------------------------------
            // EMPLOYER ACTIONS
            // ------------------------------------------------
            if (
                localStorage.getItem("role") ===
                "Employer"
            ) {

                if (
                    session.work_status ===
                    "IN_PROGRESS"
                ) {

                    actionHTML = `
                        <div
                            class="applicant-actions">

                            <button
                                class="primary-btn"
                                onclick="openCompleteWorkSession(
                                    ${session.session_id}
                                )">

                                <span class="material-symbols-outlined">
                                    task_alt
                                </span>

                                Complete Work

                            </button>
                        </div>
                    `;
                }

                else if (
                    session.work_status ===
                    "COMPLETED"
                ) {

                    actionHTML = `
                        <div
                            class="applicant-actions">

                            <button
                                class="primary-btn"
                                onclick="calculateWage(
                                    ${session.session_id}
                                )">

                                <span class="material-symbols-outlined">
                                    calculate
                                </span>

                                Calculate Wage

                            </button>
                        </div>
                    `;
                }
            }

            card.innerHTML = `
                <div
                    class="applicant-card-header">

                    <div>
                        <h3>
                            ${escapeHtml(
                                session.job_title ||
                                "Job"
                            )}
                        </h3>

                        <p>
                            Work Session #${session.session_id}
                        </p>
                    </div>

                    <span
                        class="application-status">

                        ${escapeHtml(
                            session.work_status ||
                            "UNKNOWN"
                        )}
                    </span>
                </div>

                <div
                    class="applicant-details">

                    <p>
                        📅
                        <strong>Work Date:</strong>

                        ${
                            session.work_date
                                ? formatDate(
                                    session.work_date
                                )
                                : "Not specified"
                        }
                    </p>

                    <p>
                        🕐
                        <strong>Start:</strong>

                        ${
                            session.start_time
                                ? formatDateTime(
                                    session.start_time
                                )
                                : "Not started"
                        }
                    </p>

                    <p>
                        🕐
                        <strong>End:</strong>

                        ${
                            session.end_time
                                ? formatDateTime(
                                    session.end_time
                                )
                                : "Not completed"
                        }
                    </p>

                    <p>
                        ⏱
                        <strong>Hours Worked:</strong>

                        ${
                            session.hours_worked !== null &&
                            session.hours_worked !== undefined
                                ? escapeHtml(
                                    String(
                                        session.hours_worked
                                    )
                                )
                                : "Not recorded"
                        }
                    </p>

                    <p>
                        👤
                        <strong>Attendance:</strong>

                        ${escapeHtml(
                            session.attendance_status ||
                            "Not recorded"
                        )}
                    </p>

                    ${
                        session.employer_notes
                            ? `
                                <p>
                                    📝
                                    <strong>Employer Notes:</strong>

                                    ${escapeHtml(
                                        session.employer_notes
                                    )}
                                </p>
                            `
                            : ""
                    }

                    ${actionHTML}
                </div>
            `;

            container.appendChild(
                card
            );
        }
    );
}


// ============================================================
// OPEN COMPLETE WORK SESSION
function openCompleteWorkSession(sessionId) {
    document.getElementById(
        "workSessionModal"
    ).style.display = "flex";

    document.getElementById(
        "workSessionDetails"
    ).innerHTML = `

        <div class="job-empty-state">
            <span class="material-symbols-outlined">
                task_alt
            </span>

            <h3>
                Complete Work Session
            </h3>

            <p>
                Enter the actual hours worked and any
                relevant work notes.
            </p>
        </div>
    `;

    document.getElementById(
        "workCompletionFields"
    ).style.display = "block";

    document.getElementById(
        "hoursWorked"
    ).value = "";

    document.getElementById(
        "employerNotes"
    ).value = "";

    document.getElementById(
        "workSessionActions"
    ).innerHTML = `

        <button
            class="primary-btn"
            onclick="completeWorkSession(
                ${sessionId}
            )">

            <span class="material-symbols-outlined">
                task_alt
            </span>

            Mark Work Completed

        </button>
    `;
}


// ============================================================
// COMPLETE WORK SESSION
async function completeWorkSession(sessionId) {
    const employerEmail =
        localStorage.getItem("email");

    if (!employerEmail) {
        alert(
            "Please log in again."
        );
        return;
    }

    const hoursInput =
        document.getElementById(
            "hoursWorked"
        );

    const notesInput =
        document.getElementById(
            "employerNotes"
        );

    const hoursWorked =
        hoursInput.value.trim();

    const employerNotes =
        notesInput.value.trim();

    if (!hoursWorked) {
        alert(
            "Please enter the hours worked."
        );

        hoursInput.focus();
        return;
    }

    const hours =
        Number(hoursWorked);

    if (
        Number.isNaN(hours) ||
        hours < 0 ||
        hours > 24
    ) {

        alert(
            "Hours worked must be between 0 and 24."
        );
        return;
    }

    if (
        !confirm(
            "Mark this work session as completed?"
        )
    ) {
        return;
    }

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/complete_work_session`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        session_id:
                            sessionId,

                        employer_email:
                            employerEmail,

                        hours_worked:
                            hours,

                        employer_notes:
                            employerNotes
                    })
                }
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            !data.success
        ) {

            alert(
                data.message ||
                "Unable to complete work session."
            );
            return;
        }

        alert(
            "Work session completed successfully."
        );

        closeWorkSessionModal();

        await loadWorkSessions();

        await loadMyAssignments();
    }

    catch (error) {
        console.error(
            "Complete work error:",
            error
        );

        alert(
            "Unable to connect to server."
        );
    }
}


// ============================================================
// LOAD EMPLOYER DUE WAGES
// ============================================================
async function loadEmployerPayments() {
    const email =
        localStorage.getItem(
            "email"
        );

    if (!email) {
        alert(
            "Please log in again."
        );
        return;
    }

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/get_due_wages?email=${encodeURIComponent(email)}`
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            !data.success
        ) {
            alert(
                data.message ||
                "Unable to load due wages."
            );
            return;
        }

        const dueWages =
            data.wages || [];

        if (
            dueWages.length === 0
        ) {
            alert(
                "There are no wages currently due for payment."
            );
            return;
        }

        /*
         * For now we process the first due wage.
         *
         * Later we can replace this with a proper
         * payment-selection modal if multiple wages
         * are due.
         */
        const wage =
            dueWages[0];

        const amount =
            Number(
                wage.wage_earned || 0
            );

        const beneficiaryName =
            wage.beneficiary_name ||
            "the beneficiary";

        if (
            !confirm(
                `Record payment of ₹${amount.toLocaleString("en-IN")} to ${beneficiaryName}?`
            )
        ) {
            return;
        }

        await recordPayment(
            wage.wage_id
        );
    }

    catch (error) {
        console.error(
            "Employer due wage loading error:",
            error
        );

        alert(
            "Unable to connect to server."
        );
    }
}


// ============================================================
// CLOSE PAYMENTS MODAL
// ============================================================
function closePaymentsModal() {
    const modal =
        document.getElementById(
            "paymentsModal"
        );

    if (modal) {
        modal.style.display =
            "none";
    }
}

// ============================================================
// CLOSE ASSISTED PAYMENTS MODAL
// ============================================================
function closeAssistedPaymentsModal() {
    const modal =
        document.getElementById(
            "assistedPaymentsModal"
        );

    if (modal) {
        modal.style.display =
            "none";
    }
}

// ============================================================
// CLOSE WORK SESSION MODAL
// ============================================================
function closeWorkSessionModal() {
    const modal =
        document.getElementById(
            "workSessionModal"
        );

    if (modal) {
        modal.style.display =
            "none";
    }

    const completionFields =
        document.getElementById(
            "workCompletionFields"
        );

    if (completionFields) {
        completionFields.style.display =
            "none";
    }

    const actions =
        document.getElementById(
            "workSessionActions"
        );

    if (actions) {
        actions.innerHTML =
            "";
    }
}

// ============================================================
// CLOSE ACTIVE LOCATIONS MODAL
// ============================================================
function closeActiveLocationsModal() {
    const modal =
        document.getElementById(
            "activeLocationsModal"
        );

    if (modal) {
        modal.style.display =
            "none";
    }
}