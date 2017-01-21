function get(func, url) {
    // TODO: Add progess bar or loading icon.

    var xmlhttp = new XMLHttpRequest();
    xmlhttp.open("GET", url);
    xmlhttp.onreadystatechange = function()
    {
        if ((xmlhttp.status == 200) && (xmlhttp.readyState == 4)) {
            func(xmlhttp.responseText);
        } else if (xmlhttp.status == 404) {
	    alert("Sorry, we couldn't find your text.")
	    console.log(xmlhttp);
	} else if (xmlhttp.status == 500) {
	    alert("Oops, something went wrong! Try again.")
	    console.log(xmlhttp);
	}
    };
    xmlhttp.send();
}

function post(data, csrftoken, func, url) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", url, true);
    xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
    xhr.setRequestHeader('X-CSRFToken', csrftoken);
    
    // send the collected data as JSON
    xhr.send(JSON.stringify(data));    
    xhr.onloadend = func;
}
