async function registerBeneficiary(){

    const name =
    document.getElementById(
    "beneficiaryName").value;

    const phone =
    document.getElementById(
    "beneficiaryPhone").value;

    const location =
    document.getElementById(
    "beneficiaryLocation").value;

    const support =
    document.getElementById(
    "beneficiarySupport").value;

    if(
        !name ||
        !phone ||
        !location
    ){
        alert(
        "Please fill all fields");
        return;
    }

    try{

        const response =
        await fetch(
        `${API_BASE_URL}/register_beneficiary`,
        {
            method:"POST",
            headers:{
              "Content-Type":
              "application/json"
            },
            body:JSON.stringify({
                email:localStorage.getItem("email"),
                name:name,
                phone:phone,
                location:location,
                support:support
            })
        });

        const data =
        await response.json();

        if(response.ok){
            showBeneficiaryPopup();
        }
        else{
            alert(data.message || "Registration Failed");
            return;
        }

        document.getElementById(
        "beneficiaryName").value="";

        document.getElementById(
        "beneficiaryPhone").value="";

        document.getElementById(
        "beneficiaryLocation").value="";

    }
    catch(error){

        alert(
        "Backend Error");

        console.log(error);
    }
}

function showBeneficiaryPopup(){

    document.getElementById(
    "beneficiaryPopup").style.display = "flex";

}

function closeBeneficiaryPopup(){

    document.getElementById(
    "beneficiaryPopup").style.display = "none";

}