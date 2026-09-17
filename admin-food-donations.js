// ==========================================
// ADMIN FOOD DONATION MANAGEMENT
async function loadAdminDonations() {
    const container =
        document.getElementById(
            "adminDonationList"
        );

    if (!container) {
        return;
    }

    try {
        const adminEmail =
            localStorage.getItem("email");

        const response =
            await fetch(
                `${API_BASE_URL}/api/admin/donations?email=${encodeURIComponent(adminEmail)}`
            );

        const data =
            await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.message ||
                "Unable to load donations."
            );
        }

        const donations =
            data.donations;

        if (!donations.length) {
            container.innerHTML = `
                <p class="donation-empty">
                    No food donations found.
                </p>
            `;
            return;
        }

        container.innerHTML =
            donations.map(
                donation => {
                    let proofHTML =
                        `<span>No proof uploaded</span>`;

                    if (
                        donation.proof_photos &&
                        donation.proof_photos.length
                    ) {

                        proofHTML =
                            donation.proof_photos
                                .map(
                                    proof => `

                                        <div
                                            style="
                                                margin-bottom:8px;
                                            "
                                        >

                                            <strong>
                                                ${escapeAdminText(
                                                    proof.full_name
                                                )}
                                            </strong>

                                            <br>

                                            <a
                                                href="${proof.proof_photo}"
                                                target="_blank"
                                                class="primary-btn"
                                            >
                                                📷 View Proof
                                            </a>

                                        </div>

                                    `
                                )
                                .join("");
                    }

                    return `

                        <div class="donation-card">
                            <div
                                class="donation-card-header"
                            >
                                <div>
                                    <h3>
                                        ${escapeAdminText(
                                            donation.food_type
                                        )}
                                    </h3>

                                    <span
                                        class="donation-id"
                                    >
                                        Donation
                                        #${donation.id}
                                    </span>
                                </div>

                                ${createAdminStatusBadge(
                                    donation.status
                                )}

                            </div>

                            <div
                                class="donation-details"
                            >
                                <div>
                                    <strong>
                                        Quantity:
                                    </strong>

                                    ${escapeAdminText(
                                        donation.quantity
                                    )}
                                </div>

                                <div>
                                    <strong>
                                        Pickup:
                                    </strong>

                                    ${escapeAdminText(
                                        donation.location
                                    )}
                                </div>

                                <div>
                                    <strong>
                                        Donor:
                                    </strong>

                                    ${escapeAdminText(
                                        donation.donor_email ||
                                        "Not available"
                                    )}
                                </div>

                                <div>
                                    <strong>
                                        Volunteer:
                                    </strong>

                                    ${escapeAdminText(
                                        donation.volunteer_name ||
                                        donation.volunteer_email ||
                                        "Not assigned"
                                    )}
                                </div>

                                <div>
                                    <strong>
                                        Beneficiaries:
                                    </strong>

                                    ${
                                        donation.distributed_beneficiaries &&
                                        donation.distributed_beneficiaries.length
                                            ?
                                            `
                                            <div style="margin-top:8px;">

                                                ${
                                                    donation.distributed_beneficiaries
                                                        .map(
                                                            beneficiary => `
                                                                <div
                                                                    style="
                                                                        margin-bottom:8px;
                                                                        padding:8px;
                                                                        border:1px solid #ddd;
                                                                        border-radius:6px;
                                                                    "
                                                                >

                                                                    <strong>
                                                                        ${escapeAdminText(
                                                                            beneficiary.full_name
                                                                        )}
                                                                    </strong>

                                                                    <br>

                                                                    Quantity:
                                                                    ${escapeAdminText(
                                                                        beneficiary.quantity_received
                                                                    )}

                                                                    <br>

                                                                    Location:
                                                                    ${escapeAdminText(
                                                                        beneficiary.location ||
                                                                        "—"
                                                                    )}

                                                                </div>
                                                            `
                                                        )
                                                        .join("")
                                                }

                                            </div>
                                            `
                                            :
                                            escapeAdminText(
                                                donation.beneficiary_name ||
                                                "Not delivered"
                                            )
                                    }
                                </div>

                                <div>
                                    <strong>
                                        Assigned At:
                                    </strong>

                                    ${escapeAdminText(
                                        formatAdminDateTime(
                                            donation.assigned_at
                                        ) 
                                    )}
                                </div>

                                <div>
                                    <strong>
                                        Picked Up At:
                                    </strong>

                                    ${escapeAdminText(
                                        formatAdminDateTime(
                                            donation.picked_up_at
                                        )
                                    )}
                                </div>

                                <div>
                                    <strong>
                                        Out for Delivery At:
                                    </strong>

                                    ${escapeAdminText(
                                        formatAdminDateTime(
                                            donation.out_for_delivery_at
                                        )
                                    )}
                                </div>

                                <div>
                                    <strong>
                                        Completed At:
                                    </strong>

                                    ${escapeAdminText(
                                        formatAdminDateTime(
                                            donation.completed_at
                                        )
                                    )}
                                </div>

                                <div>
                                    <strong>
                                        Completion Notes:
                                    </strong>

                                    ${escapeAdminText(
                                        donation.completion_notes ||
                                        "—"
                                    )}
                                </div>

                                <div>
                                    <strong>
                                        Proof Photo:
                                    </strong>

                                    ${proofHTML}
                                </div>
                            </div>
                        </div>
                    `;
                }
            ).join("");
    }

    catch (error) {
        console.error(
            "Admin donation loading error:",
            error
        );

        container.innerHTML = `
            <p class="donation-empty">
                Unable to load donation information.
            </p>
        `;
    }
}


// ==========================================
// FORMAT ADMIN DONATION DATE & TIME
function formatAdminDateTime(value) {

    if (!value) {
        return "—";
    }

    const date = new Date(value);

    if (isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit",
        hour12: true
    });
}



// ==========================================
// ADMIN DONATION STATUS BADGE
function createAdminStatusBadge(status) {
    let className =
        "status-badge";


    if (status === "Pending") {
        className +=
            " status-pending";
    }

    else if (status === "Assigned") {
        className +=
            " status-assigned";
    }

    else if (status === "Picked Up") {
        className +=
            " status-picked";
    }

    else if (
        status === "Out for Delivery"
    ) {
        className +=
            " status-delivery";
    }

    else if (status === "Completed") {

        className +=
            " status-completed";
    }

    return `
        <span class="${className}">
            ${escapeAdminText(status)}
        </span>
    `;
}


function escapeAdminText(value) {
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


document.addEventListener(
    "DOMContentLoaded",
    function () {
        const role =
            localStorage.getItem("role");

        if (role !== "Admin") {
            window.location.replace(
                "food-donation.html"
            );

            return;
        }
        loadAdminDonations();
    }
);