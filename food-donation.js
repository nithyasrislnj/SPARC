const donationProofPhotos = {};
/* async function submitDonation() {

  const foodType =
    document.getElementById("foodType").value;

  const quantity =
    document.getElementById("quantity").value;

  const expiryTime =
    document.getElementById("expiryTime").value;

  const location =
    document.getElementById("location").value;

  if (
    !foodType ||
    !quantity ||
    !expiryTime ||
    !location
  ) {
    alert("Please fill all fields");
    return;
  }

  try {

    const response = await fetch(
      `${API_BASE_URL}/add_donation`,
      {
        method: "POST",
        headers: {
          "Content-Type":
          "application/json"
        },
        body: JSON.stringify({
          email:localStorage.getItem("email"),
          food_type: foodType,
          quantity: quantity,
          expiry_time: expiryTime,
          location: location
        })
      }
    );

    const data = await response.json();

    alert(data.message);

    document.getElementById("foodType").value = "";
    document.getElementById("quantity").value = "";
    document.getElementById("expiryTime").value = "";
    document.getElementById("location").value = "";

  } catch(error) {

    alert("Backend not running");
    console.log(error);

  }
} */

// ==========================================
// SUBMIT FOOD DONATION
// Anyone who is logged in can donate
// ==========================================
async function submitDonation() {

    const foodType =
        document.getElementById("foodType").value;

    const quantity =
        document.getElementById("quantity").value;

    const expiryTime =
        document.getElementById("expiryTime").value;

    const location =
        document.getElementById("location").value;

    if (
        !foodType ||
        !quantity ||
        !expiryTime ||
        !location
    ) {
        alert("Please fill all fields");
        return;
    }

    try {

        const response = await fetch(
            `${API_BASE_URL}/add_donation`,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    email:
                        localStorage.getItem("email"),

                    food_type:
                        foodType,

                    quantity:
                        quantity,

                    expiry_time:
                        expiryTime,

                    location:
                        location
                })
            }
        );

        const data =
            await response.json();

        alert(data.message);

        if (data.message ===
            "Food Donation Submitted Successfully") {

            document.getElementById(
                "foodType"
            ).value = "";

            document.getElementById(
                "quantity"
            ).value = "";

            document.getElementById(
                "expiryTime"
            ).value = "";

            document.getElementById(
                "location"
            ).value = "";

            // If the logged-in user is a volunteer,
            // refresh their donation lists.
            if (
                localStorage.getItem("role")
                === "Volunteer"
            ) {
                loadAvailableDonations();
                loadMyDonations();
            }
        }

    } catch (error) {

        alert("Backend not running");

        console.log(error);
    }
}


// ==========================================
// INITIALIZE FOOD DONATION MODULE
document.addEventListener(
    "DOMContentLoaded",
    function () {
        const role =
            localStorage.getItem("role");

        // ADMIN
        if (role === "Admin") {
            const adminAction =
                document.getElementById(
                    "adminFoodDonationAction"
                );

            if (adminAction) {
                adminAction.style.display =
                    "block";
            }
        }

        // VOLUNTEER
        if (role === "Volunteer") {
            const volunteerActions =
                document.getElementById(
                    "volunteerFoodDonationActions"
                );

            if (volunteerActions) {
                volunteerActions.style.display =
                    "block";
            }
        }
    }
);


// ==========================================
// LOAD AVAILABLE DONATIONS
async function loadAvailableDonations() {

    const container =
        document.getElementById(
            "availableDonations"
        );

    if (!container) return;

    try {

        const response =
            await fetch(
                `${API_BASE_URL}/get_available_donations?email=${encodeURIComponent(
                    localStorage.getItem("email")
                )}`
            );

        if (!response.ok) {
            throw new Error(
                "Failed to load donations"
            );
        }

        const donations =
            await response.json();

        if (!donations.length) {

            container.innerHTML = `
                <div class="donation-empty">
                    <span class="material-symbols-outlined">
                        volunteer_activism
                    </span>

                    <p>
                        No donations are currently
                        available.
                    </p>
                </div>
            `;

            return;
        }

        container.innerHTML =
            donations.map(
                donation =>
                    createAvailableDonationCard(
                        donation
                    )
            ).join("");

    } catch (error) {

        console.error(
            "Available donations error:",
            error
        );

        container.innerHTML = `
            <div class="donation-empty">
                Unable to load donations.
                Please try again.
            </div>
        `;
    }
}


// ==========================================
// AVAILABLE DONATION CARD
function createAvailableDonationCard(
    donation
) {

    return `
        <div class="donation-card">

            <div class="donation-card-header">

                <div>
                    <h3>
                        ${escapeDonationText(
                            donation.food_type
                        )}
                    </h3>

                    <span class="donation-id">
                        Donation #${donation.id}
                    </span>
                </div>

                <span class="status-badge status-available">
                    Available
                </span>

            </div>


            <div class="donation-details">

                <div>
                    <span class="material-symbols-outlined">
                        inventory_2
                    </span>

                    <span>
                        <strong>Quantity:</strong>
                        ${escapeDonationText(
                            donation.quantity
                        )}
                    </span>
                </div>


                <div>
                    <span class="material-symbols-outlined">
                        location_on
                    </span>

                    <span>
                        <strong>Pickup:</strong>
                        ${escapeDonationText(
                            donation.location
                        )}
                    </span>
                </div>


                <div>
                    <span class="material-symbols-outlined">
                        schedule
                    </span>

                    <span>
                        <strong>Expires:</strong>
                        ${formatDonationDate(
                            donation.expiry_time
                        )}
                    </span>
                </div>

            </div>


            <button
                class="primary-btn donation-action-btn"
                onclick="takeDonation(
                    ${donation.id}
                )">

                <span class="material-symbols-outlined">
                    volunteer_activism
                </span>

                Take Responsibility

            </button>

        </div>
    `;
}


// ==========================================
// TAKE RESPONSIBILITY
async function takeDonation(
    donationId
) {

    const volunteerEmail =
        localStorage.getItem("email");

    if (!volunteerEmail) {

        alert(
            "Please login before taking responsibility."
        );

        return;
    }


    const confirmed =
        confirm(
            "Do you want to take responsibility for Donation #" +
            donationId +
            "?"
        );

    if (!confirmed) {
        return;
    }


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/take_donation/${donationId}`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        email:
                            volunteerEmail
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            alert(
                data.message ||
                "Unable to take responsibility."
            );

            return;
        }


        alert(data.message);


        // Refresh both lists
        loadAvailableDonations();
        loadMyDonations();

    } catch (error) {

        console.error(
            "Take donation error:",
            error
        );

        alert(
            "Unable to connect to the backend."
        );
    }
}


// ==========================================
// LOAD MY DONATIONS
async function loadMyDonations() {

    const container =
        document.getElementById(
            "myDonations"
        );

    if (!container) return;


    const email =
        localStorage.getItem("email");

    if (!email) {

        container.innerHTML = `
            <div class="donation-empty">
                Please login to view your donations.
            </div>
        `;

        return;
    }


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/get_my_donations/${encodeURIComponent(email)}`
            );


        if (!response.ok) {
            throw new Error(
                "Failed to load my donations"
            );
        }


        const donations =
            await response.json();


        if (!donations.length) {

            container.innerHTML = `
                <div class="donation-empty">

                    <span class="material-symbols-outlined">
                        inventory
                    </span>

                    <p>
                        You haven't taken responsibility
                        for any donations yet.
                    </p>

                </div>
            `;

            return;
        }


        container.innerHTML =
            donations.map(
                donation =>
                    createMyDonationCard(
                        donation
                    )
            ).join("");


    } catch (error) {

        console.error(
            "My donations error:",
            error
        );

        container.innerHTML = `
            <div class="donation-empty">
                Unable to load your donations.
                Please try again.
            </div>
        `;
    }
}


// ==========================================
// MY DONATION CARD
function createMyDonationCard(
    donation
) {

    let actionButton = "";

    const status =
        donation.status;


    if (status === "Assigned") {

        actionButton = `
            <button
                class="primary-btn donation-action-btn"
                onclick="pickDonation(
                    ${donation.id}
                )">

                <span class="material-symbols-outlined">
                    package_2
                </span>

                Picked Donation

            </button>
        `;

    }

    else if (status === "Picked Up") {

        actionButton = `
            <button
                class="primary-btn donation-action-btn"
                onclick="startDelivery(
                    ${donation.id}
                )">

                <span class="material-symbols-outlined">
                    local_shipping
                </span>

                Heading to Beneficiary

            </button>
        `;

    }

    else if (
        status === "Out for Delivery"
    ) {
        actionButton = `
            <button
                id="completeDonationBtn-${donation.id}"
                class="primary-btn donation-action-btn"
                onclick="openCompletionForm(
                    ${donation.id}
                )">

                <span class="material-symbols-outlined">
                    check_circle
                </span>

                Complete Donation
            </button>
        `;
    }

    else if (status === "Completed") {

        actionButton = `
            <div class="donation-completed">
                <span class="material-symbols-outlined">
                    check_circle
                </span>

                Donation Successful
            </div>
        `;
    }


    return `
        <div class="donation-card">

            <div class="donation-card-header">

                <div>

                    <h3>
                        ${escapeDonationText(
                            donation.food_type
                        )}
                    </h3>

                    <span class="donation-id">
                        Donation #${donation.id}
                    </span>

                </div>

                ${createStatusBadge(
                    status
                )}

            </div>


            <div class="donation-details">

                <div>
                    <span class="material-symbols-outlined">
                        inventory_2
                    </span>

                    <span>
                        <strong>Quantity:</strong>
                        ${escapeDonationText(
                            donation.quantity
                        )}
                    </span>
                </div>


                <div>
                    <span class="material-symbols-outlined">
                        location_on
                    </span>

                    <span>
                        <strong>Pickup:</strong>
                        ${escapeDonationText(
                            donation.location
                        )}
                    </span>
                </div>

            </div>


            <div class="donation-progress">

                ${createProgressStep(
                    "Responsibility Taken",
                    true
                )}

                ${createProgressStep(
                    "Picked Up",
                    [
                        "Picked Up",
                        "Out for Delivery",
                        "Completed"
                    ].includes(status)
                )}

                ${createProgressStep(
                    "Out for Delivery",
                    [
                        "Out for Delivery",
                        "Completed"
                    ].includes(status)
                )}

                ${createProgressStep(
                    "Donation Successful",
                    status === "Completed"
                )}

            </div>


            ${actionButton}

        </div>
    `;
}


// ==========================================
// PICK DONATION
async function pickDonation(
    donationId
) {
    const email =
        localStorage.getItem("email");

    if (!email) return;

    const confirmed =
        confirm(
            "Have you collected Donation #" +
            donationId +
            " from the donor?"
        );

    if (!confirmed) {
        return;
    }

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/pick_donation/${donationId}`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        email: email
                    })
                }
            );

        const data =
            await response.json();

        if (!response.ok) {
            alert(
                data.message ||
                "Unable to update donation."
            );

            return;
        }

        alert(data.message);

        loadMyDonations();
        loadAvailableDonations();

    } 
    catch (error) {
        console.error(
            "Pick donation error:",
            error
        );

        alert(
            "Unable to connect to the backend."
        );
    }
}


// ==========================================
// START DELIVERY
async function startDelivery(
    donationId
) {

    const email =
        localStorage.getItem("email");

    if (!email) return;


    const confirmed =
        confirm(
            "Are you heading to the beneficiary with Donation #" +
            donationId +
            "?"
        );

    if (!confirmed) {
        return;
    }


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/start_delivery/${donationId}`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        email: email
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            alert(
                data.message ||
                "Unable to start delivery."
            );

            return;
        }


        alert(data.message);

        loadAvailableDonations();
        loadMyDonations();


    } catch (error) {

        console.error(
            "Start delivery error:",
            error
        );

        alert(
            "Unable to connect to the backend."
        );
    }
}


// ==========================================
// STATUS BADGE
function createStatusBadge(
    status
) {

    let className =
        "status-badge";

    if (status === "Assigned") {
        className += " status-assigned";
    }

    else if (status === "Picked Up") {
        className += " status-picked";
    }

    else if (
        status === "Out for Delivery"
    ) {
        className += " status-delivery";
    }

    else if (status === "Completed") {
        className += " status-completed";
    }

    return `
        <span class="${className}">
            ${escapeDonationText(status)}
        </span>
    `;
}


// ==========================================
// PROGRESS STEP
function createProgressStep(
    label,
    completed
) {

    return `
        <div class="progress-step
            ${completed ? "completed" : ""}">

            <span class="progress-dot">
                ${completed ? "✓" : ""}
            </span>

            <span>
                ${label}
            </span>

        </div>
    `;
}


// ==========================================
// FORMAT DATE
function formatDonationDate(
    value
) {

    if (!value) {
        return "Not specified";
    }

    const date =
        new Date(value);

    if (isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString(
        [],
        {
            dateStyle: "medium",
            timeStyle: "short"
        }
    );
}


// ==========================================
// BASIC HTML ESCAPING
function escapeDonationText(
    value
) {

    if (
        value === null ||
        value === undefined
    ) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// ==========================================
// OPEN COMPLETION FORM
async function openCompletionForm(donationId) {
    // Prevent multiple completion forms
    const existingForm =
        document.getElementById(
            `completionForm-${donationId}`
        );

    if (existingForm) {
        existingForm.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });
        return;
    }

    // Disable the Complete Donation button
    const completeButton =
        document.getElementById(
            `completeDonationBtn-${donationId}`
        );

    if (completeButton) {
        completeButton.disabled = true;
        completeButton.style.opacity = "0.6";
        completeButton.style.cursor = "not-allowed";
    }

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/get_beneficiaries`
            );

        if (!response.ok) {
            throw new Error(
                "Failed to load beneficiaries"
            );
        }

        const beneficiaries =
            await response.json();


        if (!beneficiaries.length) {
            alert(
                "No available beneficiaries found."
            );

            if (completeButton) {
                completeButton.disabled = false;
                completeButton.style.opacity = "1";
                completeButton.style.cursor = "pointer";
            }

            return;
        }

        const beneficiaryOptions =
            beneficiaries.map(
                beneficiary => `
                    <option
                        value="${beneficiary.id}">

                        ${escapeDonationText(
                            beneficiary.full_name
                        )}
                        -
                        ${escapeDonationText(
                            beneficiary.location
                        )}

                    </option>
                `
            ).join("");

        const container =
            document.getElementById(
                "myDonations"
            );

        container.insertAdjacentHTML(
            "afterbegin",

            `
            <div
                id="completionForm-${donationId}"
                class="completion-form">

                <div
                    class="completion-form-header">

                    <h3>
                        Complete Donation
                    </h3>

                    <span>
                        Donation #${donationId}
                    </span>
                </div>

                <label>
                    Select Beneficiary
                </label>

                <select
                    id="beneficiary-${donationId}"
                    required
                    onchange="updateDonationCompletionButton(
                    ${donationId})">

                    <option value="">
                        Select a beneficiary
                    </option>

                    ${beneficiaryOptions}
                </select>


                <label>
                    Donation Proof Photo
                </label>

                <button
                    type="button"
                    class="outline-btn"
                    onclick="openProofUploader(
                        ${donationId}
                    )">

                    <span
                        class="material-symbols-outlined">
                        photo_camera
                    </span>
                    Upload Donation Photo
                </button>

                <div
                    id="proofPreview-${donationId}"
                    class="proof-preview">

                    No photo uploaded yet.
                </div>

                <label>
                    Completion Notes
                </label>

                <textarea
                    id="completionNotes-${donationId}"
                    rows="4"
                    placeholder="Describe the donation delivery..."
                    required
                    oninput="updateDonationCompletionButton(
                    ${donationId})">
                </textarea>

                <div
                    class="completion-actions">
                    <button
                        type="button"
                        class="outline-btn"
                        onclick="closeCompletionForm(
                            ${donationId}
                        )">
                        Cancel
                    </button>

                    <button
                        type="button"
                        id="donationSuccessfulBtn-${donationId}"
                        class="primary-btn"
                        onclick="submitDonationCompletion(
                            ${donationId}
                        )"
                        disabled>

                        Donation Successful

                    </button>
                </div>
            </div>
            `
        );

        // Scroll to form
        document
            .getElementById(
                `completionForm-${donationId}`
            )
            .scrollIntoView({
                behavior: "smooth",
                block: "center"
            });

    } 
    catch (error) {
        console.error(
            "Beneficiary loading error:",
            error
        );

        if (completeButton) {
            completeButton.disabled = false;
            completeButton.style.opacity = "1";
            completeButton.style.cursor = "pointer";
        }

        alert(
            "Unable to load beneficiaries."
        );
    }
}


// ==========================================
// UPDATE DONATION COMPLETION BUTTON
function updateDonationCompletionButton(
    donationId
) {
    const beneficiaryElement =
        document.getElementById(
            `beneficiary-${donationId}`
        );

    const notesElement =
        document.getElementById(
            `completionNotes-${donationId}`
        );

    const submitButton =
        document.getElementById(
            `donationSuccessfulBtn-${donationId}`
        );

    if (
        !beneficiaryElement ||
        !notesElement ||
        !submitButton
    ) {
        return;
    }

    const beneficiary =
        beneficiaryElement.value.trim();

    const notes =
        notesElement.value.trim();

    const proofPhoto =
        donationProofPhotos[
            donationId
        ];

    const ready =
        beneficiary &&
        notes &&
        proofPhoto;

    submitButton.disabled = !ready;

    if (ready) {
        submitButton.style.opacity = "1";
        submitButton.style.cursor = "pointer";
    } else {
        submitButton.style.opacity = "0.6";
        submitButton.style.cursor = "not-allowed";
    }
}


// ==========================================
// CLOSE COMPLETION FORM
function closeCompletionForm(
    donationId
) {
    const form =
        document.getElementById(
            `completionForm-${donationId}`
        );

    if (form) {
        form.remove();
    }

    const completeButton =
        document.getElementById(
            `completeDonationBtn-${donationId}`
        );

    if (completeButton) {
        completeButton.disabled = false;
        completeButton.style.opacity = "1";
        completeButton.style.cursor = "pointer";
    }

    delete donationProofPhotos[
        donationId
    ];
}



// ==========================================
// SUBMIT DONATION COMPLETION
async function submitDonationCompletion(
    donationId
) {
    const email =
        localStorage.getItem("email");

    const beneficiary =
        document.getElementById(
            `beneficiary-${donationId}`
        ).value;

    const notes =
        document.getElementById(
            `completionNotes-${donationId}`
        ).value.trim();

    const proofPhoto =
        donationProofPhotos[
            donationId
        ];

    // ------------------------------
    // VALIDATION
    // ------------------------------
    if (!beneficiary) {
        alert(
            "Please select a beneficiary."
        );
        return;
    }

    if (!proofPhoto) {
        alert(
            "Please upload a donation proof photo."
        );

        return;
    }

    const confirmed =
        confirm(
            "Are you sure the donation has been successfully delivered?"
        );

    if (!confirmed) {
        return;
    }

    try {
        const response =
            await fetch(
                `${API_BASE_URL}/complete_donation/${donationId}`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        email: email,

                        beneficiary_id:
                            beneficiary,

                        proof_photo:
                            proofPhoto,

                        completion_notes:
                            notes
                    })
                }
            );

        const data =
            await response.json();

        if (!response.ok) {
            alert(
                data.message ||
                "Unable to complete donation."
            );

            return;
        }

        alert(
            data.message
        );

        delete donationProofPhotos[
            donationId
        ];

        loadAvailableDonations();

        loadMyDonations();
    } 

    catch (error) {
        console.error(
            "Completion error:",
            error
        );
        alert(
            "Unable to connect to the backend."
        );
    }
}


// ==========================================
// CLOUDINARY DONATION PROOF UPLOADER
// SIGNED UPLOAD
// ==========================================
async function openProofUploader(donationId) {
    if (!window.cloudinary) {
        alert(
            "Cloudinary upload system is not loaded."
        );
        return;
    }

    try {
        const timestamp =
            Math.floor(Date.now() / 1000);

        // Ask Flask backend for a signed upload
        const signResponse =
            await fetch(
                `${API_BASE_URL}/api/cloudinary/sign`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        timestamp: timestamp,
                        upload_preset:
                            "sparc_donation_proof"
                    })
                }
            );

        const signData =
            await signResponse.json();

        if (
            !signResponse.ok ||
            !signData.success
        ) {

            console.error(
                "Cloudinary signature error:",
                signData
            );

            alert(
                "Unable to prepare secure photo upload."
            );

            return;
        }

        const widget =
            cloudinary.createUploadWidget(
                {
                    cloudName:
                        signData.cloud_name,

                    apiKey:
                        signData.api_key,

                    uploadPreset:
                        "sparc_donation_proof",

                    sources: [
                        "local",
                        "camera"
                    ],

                    multiple: false,
                    maxFiles: 1,
                    resourceType: "image",

                    clientAllowedFormats: [
                        "jpg",
                        "jpeg",
                        "png",
                        "webp"
                    ],

                    maxFileSize: 5000000,

                    folder:
                        "sparc/donation_proofs",

                    uploadSignature:
                        signData.signature,

                    uploadSignatureTimestamp:
                        signData.timestamp
                },

                function(error, result) {
                    if (error) {
                        console.error(
                            "Cloudinary error:",
                            error
                        );

                        alert(
                            "Photo upload failed."
                        );

                        return;
                    }

                    if (
                        result &&
                        result.event === "success"
                    ) {

                        const imageUrl =
                            result.info.secure_url;

                        // Store proof URL for this donation
                        donationProofPhotos[
                            donationId
                        ] = imageUrl;

                        // Enable Donation Successful
                        // if all required details are filled
                        updateDonationCompletionButton(
                            donationId
                        );

                        // Show preview
                        const preview =
                            document.getElementById(
                                `proofPreview-${donationId}`
                            );

                        if (preview) {

                            preview.innerHTML = `
                                <img
                                    src="${imageUrl}"
                                    alt="Donation proof"
                                    class="proof-image">

                                <p>
                                    ✓ Photo uploaded successfully
                                </p>
                            `;
                        }

                        alert(
                            "Donation proof photo uploaded successfully!"
                        );
                    }
                }
            );
        widget.open();

    } 
    catch (error) {
        console.error(
            "Cloudinary upload error:",
            error
        );

        alert(
            "Unable to upload donation proof photo."
        );
    }
}