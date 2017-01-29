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
		alert("It looks like you don't have access to this text. If you do, please login.")
		console.log(xhr);
            } else if (xhr.status === 404) {
		alert("Sorry, we couldn't find your text.")
		console.log(xhr);
	    } else if (xhr.status === 500) {
		alert("Oops, something went wrong! Try again.")
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
		//alert("Warning: It looks like you don't have access to this text. None of the changes you make will be saved. If you do, please login.")
		console.log(xhr);
            } else if (xhr.status === 404) {
		alert("Sorry, we couldn't find your text.")
		console.log(xhr);
	    } else if (xhr.status === 500) {
		alert("Oops, something went wrong! Try again.")
		console.log(xhr);
	    }
	}
    };
    xhr.send(JSON.stringify(data));    
}
