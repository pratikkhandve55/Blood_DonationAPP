function getLocation(latId, lngId) {

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {

            document.getElementById(latId).value = position.coords.latitude;
            document.getElementById(lngId).value = position.coords.longitude;

            alert("Location captured successfully!");

        }, function(error) {
            alert("Error getting location");
        });

    } else {
        alert("Geolocation is not supported by this browser.");
    }
}