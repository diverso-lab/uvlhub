function test_zenodo_connection() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/zenodo/test', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var response = JSON.parse(xhr.responseText);
            if (!response.success) {
                document.getElementById("test_zenodo_connection_error").style.display = "block";
                console.log(response);
                console.log(response.success);
                console.log(response.messages);
            }
        } else if (xhr.readyState === 4 && xhr.status !== 200) {
            console.error('Error:', xhr.status);
        }
    };
    xhr.send();
}
