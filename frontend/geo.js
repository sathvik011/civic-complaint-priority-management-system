// geo.js

document.addEventListener("DOMContentLoaded", () => {
  const locationInput = document.getElementById("complaint-location");
  const getLocationBtn = document.createElement("button");
  getLocationBtn.type = "button";
  getLocationBtn.textContent = "📍 Use My Location";
  getLocationBtn.id = "getLocationBtn";
  getLocationBtn.style.marginLeft = "10px";

  if (locationInput) {
    // Add the button to the page
    locationInput.insertAdjacentElement("afterend", getLocationBtn);

    getLocationBtn.addEventListener("click", () => {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            
            // Store coordinates in sessionStorage
            sessionStorage.setItem('complaintCoords', JSON.stringify({ lat, lng }));

            locationInput.value = `Lat: ${lat.toFixed(5)}, Lng: ${lng.toFixed(5)}`;
            alert("Location captured successfully!");
          },
          (error) => {
            console.error("Geolocation error:", error);
            alert("Unable to fetch location. Please enter manually.");
          }
        );
      } else {
        alert("Geolocation is not supported by this browser.");
      }
    });
  }
});