var corpus_id = "";
var base_url = "";

function text_visualization(text_url, b_url, cid) {
    corpus_id = cid;
    base_url = b_url;
    _get(_display_content, text_url);
}

function _get(func, url) {
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

function _content_in_elem(elem_id, content_json) {
    var text_elem = document.getElementById(elem_id);
    // Inserted HTML as string for fastest document rendering.
    var content = "";
    for (var t = 0; t < content_json.tokens.length; t++) {
	var seq = content_json.tokens[t].seq;
	var word = content_json.tokens[t].word;
	var token = document.createElement("span");
	token.className = "seq" + seq
	token.textContent = word;
	token.onmouseover = _hover_highlight;
	token.onmouseout = _hover_unhighlight;
	text_elem.appendChild(token);
    }
}

function _display_content(responseText) {
    var content_json = JSON.parse(responseText);
    _content_in_elem("text", content_json);
}

function load_base() {
    var text_elem = document.getElementById("text");
    text_elem.style.cssFloat = "left";
    text_elem.style.paddingRight = "0";
    text_elem.style.width = "48%";

    var wrapper = document.getElementById("contain");
    wrapper.style.width = "70%";
    _get(_display_base, base_url);
}

function _display_base(responseText) {
    var base_json = JSON.parse(responseText);
    var base_elem = document.getElementById("base_text");
    base_elem.style.width = "48%";
    _content_in_elem("base_text", base_json);
}

function _hover_highlight(event) {
    var seq = this.className.replace(/seq/, "");
    var words = document.getElementsByClassName("seq" + seq);
    console.log(seq);
    for (var w = 0; w < words.length; w++) {
	words[w].style.borderBottom = "black 3px solid";
    }
}

function _hover_unhighlight(event) {
    var seq = this.className.replace(/seq/, "");
    var words = document.getElementsByClassName("seq" + seq);
    for (var w = 0; w < words.length; w++) {
	words[w].style.borderBottom = "none";
    }
}
