const testZenodoConnection = () => {
    console.log('Testing Zenodo connection...');
    const xhr = new XMLHttpRequest();
    xhr.open('GET', '/zenodo/test', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = () => {
        if (xhr.readyState === 4 && xhr.status === 200) {
            const response = JSON.parse(xhr.responseText);
            if (!response.success) {
                document.getElementById("test_zenodo_connection_error").style.display = "block";
                console.log(response);
                console.log(response.success);
                console.log(response.messages);
            }
            console.log('Testing Zenodo connection... OK');
        } else if (xhr.readyState === 4 && xhr.status !== 200) {
            console.error('Error:', xhr.status);
        }
    };
    xhr.send();
};
