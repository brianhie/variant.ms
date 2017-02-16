function get(func, url) {
    // TODO: Add progess bar or loading icon.

    var xhr = new XMLHttpRequest();
    xhr.open("GET", url);
    xhr.onreadystatechange = function()
    {
	if (xhr.readyState === 4 || xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
		func(xhr.responseText);
            } else if (xhr.status === 403) {
		alert("Access denied",
		      "It looks like you don't have permission to make changes to this text. If you do, please login.")
		console.log(xhr);
            } else if (xhr.status === 404) {
		alert("Not found", "Sorry, we couldn't find your text.")
		console.log(xhr);
	    } else if (xhr.status === 500) {
		alert("Oops, something went wrong!",
		      "Reload the page and try again. If the problem persists, contact us.")
		console.log(xhr);
	    }
	}
    };
    xhr.send();
}

function post(data, csrftoken, func, url) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", url, true);
    xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
    xhr.setRequestHeader('X-CSRFToken', csrftoken);
    xhr.onloadend = function()
    {
	if (xhr.readyState === 4 || xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
		func(xhr.responseText);
            } else if (xhr.status === 403) {
		alert("Access denied",
		      "It looks like you don't have permission to make changes to this text. If you do, please login.")
		console.log(xhr);
            } else if (xhr.status === 404) {
		alert("Not found", "Sorry, we couldn't find your text.");
		console.log(xhr);
	    } else if (xhr.status === 400 || xhr.status === 500) {
		alert("Oops, something went wrong!",
		      "Reload the page and try again. If the problem persists, contact us.")
		console.log(xhr);
	    }
	}
    };
    xhr.send(JSON.stringify(data));    
}
