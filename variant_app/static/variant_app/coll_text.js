var corpus_id = "";
var tokens_url = "";
var last_event = null;

function coll_text_visualization(text_url, t_url, cid) {
    corpus_id = cid;
    tokens_url = _base_tokens_url(t_url);
    _get(_display_content, text_url);
}

function _base_tokens_url(t_url) {
    var arr = t_url.replace(/\/$/g, '').split('/');
    console.log(arr);
    arr.pop();
    return arr.join('/');
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
	} else if (xmlhttp.status == 500) {
	    alert("Oops, something went wrong! Try agai.")
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
	content += ("<span onmouseenter=\"_hover_highlight(" + seq + ");\" " +
		    "onmouseout=\"_hover_unhighlight(" + seq + ");\" " +
		    "onclick=\"_load_tokens(event, " + seq + ");\" " +
		    "class=\"seq" + seq + "\">" + word + "</span>");
    }
    text_elem.innerHTML = content;
}

function _display_content(responseText) {
    var content_json = JSON.parse(responseText);
    _content_in_elem("text", content_json);
}

function _hover_highlight(seq) {
    var words = document.getElementsByClassName("seq" + seq);
    for (var w = 0; w < words.length; w++) {
	words[w].style.backgroundColor = "#bbb";
    }
}

function _hover_unhighlight(seq) {
    var words = document.getElementsByClassName("seq" + seq);
    for (var w = 0; w < words.length; w++) {
	words[w].style.backgroundColor = "#fff";
    }
}

function _display_tokens(responseText) {
    var content_json = JSON.parse(responseText);
    console.log(content_json);

    console.log(last_event);
    var top = last_event.layerY;

    var token_list = document.createElement("ol");
    token_list.style.position = "absolute";
    token_list.style.top = top;
    token_list.style.paddingLeft = "30px";
    token_list.style.margin = "0";

    var tokens = content_json.tokens;
    for (var t = 0; t < content_json.tokens.length; t++) {
	var token = document.createElement("li");
	token.innerHTML = tokens[t].word + " (from " + tokens[t].text_name + ")";
	token_list.appendChild(token);
    }

    var annotation = document.getElementById("annotation");
    annotation.appendChild(token_list);
}

function _load_tokens(event, seq) {
    var url = tokens_url + '/' + seq + '/';
    last_event = event;

    var annotation = document.getElementById("annotation");
    annotation.innerHTML = "";

    _get(_display_tokens, url);
}
