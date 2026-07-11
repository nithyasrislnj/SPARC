let selectedJobId = null;

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
}