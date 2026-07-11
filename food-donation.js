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
}