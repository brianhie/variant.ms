var corpus_id = "";
var tokens_url = "";
var last_event = null;
var highlight_on = true;
var variant_texts = null;

var selected = null;

function coll_text_visualization(text_url, t_url, cid) {
    corpus_id = cid;
    tokens_url = _base_tokens_url(t_url);

    document.addEventListener("DOMContentLoaded", function() {
	var checkbox = document.getElementById("cb");
	checkbox.onclick = _toggle_highlighting;

	var annotation = document.getElementById("annotation");
	variant_texts = annotation.childNodes[1];
	annotation.innerHTML = "";
	document.body.onclick = _variant_texts_side;

	_get(_display_content, text_url);
    });
}

function _base_tokens_url(t_url) {
    var arr = t_url.replace(/\/$/g, '').split('/');
    arr.pop();
    arr.pop();
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

function _var_color(variability) {
    var factor = 0.45;
    var scaled = (variability * factor) + (1 - factor);
    var rg = parseInt(scaled * 255);
    return "rgb(" + rg + "," + rg + ", 255)";
}

function _content_in_elem(elem_id, content_json) {
    var text_elem = document.getElementById(elem_id);
    // Inserted HTML as string for fastest document rendering.

    var min_len = 10;
    var max_len = 30;

    var tokens = [];
    for (var t = 0; t < content_json.tokens.length; t++) {
	var seq = content_json.tokens[t].seq;
	var word = content_json.tokens[t].word;
	var variability = parseFloat(content_json.tokens[t].variability);

	var token = document.createElement("span");
	token.id = "seq" + seq
	token.className = "coll_token"
	if (word.replace(/\s+/g,'') != "") {
	    token.style.backgroundColor = _var_color(variability);
	}
	token.prev_color = token.style.backgroundColor;
	token.textContent = word;
	token.onclick = _load_tokens;
	token.onmouseover = _hover_highlight;
	token.onmouseout = _hover_unhighlight;
	text_elem.appendChild(token);
    }
}

function _display_content(responseText) {
    var content_json = JSON.parse(responseText);
    _content_in_elem("text", content_json);
    _variant_texts_side();
}

function _hover_highlight(event) {
    this.style.borderBottom = "black 3px solid";
}

function _hover_unhighlight(event) {
    if (this != selected) {
	this.style.borderBottom = "none";
    }
}

function _display_tokens(responseText) {
    var content_json = JSON.parse(responseText);

    var top = last_event.pageY;

    var sequence_list = document.createElement("table");
    sequence_list.className = "annotate_block"
    sequence_list.style.top = top;

    for (var s = 0; s < content_json.sequences.length; s++) {
	var sequence = content_json.sequences[s];
	var sequence_row = document.createElement("tr")

	var text_span = document.createElement("td");
	if (sequence.is_base) {
	    text_span.textContent = "Base text";
	} else {
	    text_span.textContent = sequence.text_name;
	}
	text_span.className = "annotate_name sans_font"
	sequence_row.appendChild(text_span);

	var sequence_elem = document.createElement("td");
	sequence_elem.className = "annotate_text text_font"
	for (var t = 0; t < sequence.tokens.length; t++) {
	    var token = sequence.tokens[t];
	    var span = document.createElement("span");
	    span.textContent = token.word
	    if (token.is_center) {
		span.style.fontWeight = "bold";
	    }
	    sequence_elem.appendChild(span);
	}
	sequence_row.appendChild(sequence_elem);

	sequence_list.appendChild(sequence_row);
    }

    var annotation = document.getElementById("annotation");
    annotation.appendChild(sequence_list);
}

function _load_tokens(event) {
    if (selected != null)
	selected.style.borderBottom = "none";
        this.style.borderBottom = "black 3px solid";
    selected = this;

    var seq = parseInt(this.id.replace(/seq/, ''));
    var seq_start = seq - 5
    var seq_end = seq + 5
    var url = tokens_url + '/' + seq_start + '/' + seq_end + '/' + seq + '/';
    last_event = event;

    var annotation = document.getElementById("annotation");
    annotation.innerHTML = "";
    event.stopPropagation();
    //window.event.cancelBubble = true;

    _get(_display_tokens, url);
}

function _toggle_highlighting(event) {
    var tokens = document.getElementsByClassName("coll_token");
    console.log(tokens);
    if (highlight_on) {
	for (var t = 0; t < tokens.length; t++) {
	    tokens[t].style.backgroundColor = "#fff";
	}
    } else {
	for (var t = 0; t < tokens.length; t++) {
	    tokens[t].style.backgroundColor = tokens[t].prev_color;
	}
    }
    highlight_on = !highlight_on;
}

function _variant_texts_side() {
    var annotation = document.getElementById("annotation");
    annotation.innerHTML = "";
    annotation.appendChild(variant_texts);
    if (selected != null) {
	selected.style.borderBottom = "none";
	selected = null;
    }
}
