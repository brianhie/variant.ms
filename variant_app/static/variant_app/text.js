var corpus_id = "";
var base_url = "";
var base_on = false;
var manual_coll_url = "";
var highlight_on = false;
var old_width = "";

function text_visualization(text_url, b_url, mc_url, cid) {
    corpus_id = cid;

    base_url = b_url;
    manual_coll_url = mc_url;

    document.addEventListener("DOMContentLoaded", function() {
	old_width = document.getElementById("variant_head").style.maxWidth;

	var var_cb = document.getElementById("var_cb");
	if (var_cb != null)
	    var_cb.onclick = _toggle_highlighting;

	var base_cb = document.getElementById("base_cb");
	if (base_cb != null)
	    base_cb.onclick = _toggle_base;

	get(_display_content, text_url);
    });
}


function _var_color(variability) {
    if (!variability) {
	return "#fff";
    }
    var factor = 0.45;
    var scaled = (variability * factor) + (1 - factor);
    var rg = parseInt(scaled * 255);
    return "rgb(" + rg + "," + rg + ", 255)";
}

function _content_in_elem(elem_id, content_json) {
    var text_elem = document.getElementById(elem_id);
    var elements = text_elem.getElementsByClassName("loader");
    while(elements.length > 0){
        elements[0].parentNode.removeChild(elements[0]);
    }

    var content = "";
    for (var t = 0; t < content_json.tokens.length; t++) {
	var seq = content_json.tokens[t].seq;
	var coll_token_seq = content_json.tokens[t].coll_token_seq;
	var word = content_json.tokens[t].word;
	var token = document.createElement("span");
	var variability = parseFloat(content_json.tokens[t].variability);

	token.className = "seq" + coll_token_seq
	token.textContent = word;
	token.onmouseover = _hover_highlight;
	token.onmouseout = _hover_unhighlight;

	if (word.replace(/\s+/g,'') != "") {
	    token.prev_color = _var_color(variability);
	} else if (word.replace(/[ \t\r]+/g, '') != "") {
	    token.textContent = word.replace(/[ \t\r]+/g, '');
	}

	if (elem_id == "base_text") {
	    token.ondragover = _drag_over_token;
	    token.ondragleave = _drag_leave_token;
	    token.ondrop = _drop_token;
	} else {
	    token.draggable = true;
	    token.ondragstart = _drag_token;
	    token.text_seq = seq;
	    token.id = "textSeq" + seq;
	}

	text_elem.appendChild(token);
    }
}

function _display_content(responseText) {
    var content_json = JSON.parse(responseText);
    _content_in_elem("text", content_json);
}

function _hover_highlight(event) {
    if (!base_on)
	return;

    var seq = this.className.replace(/seq/, "");
    var words = document.getElementsByClassName("seq" + seq);
    for (var w = 0; w < words.length; w++) {
	words[w].style.borderBottom = "black 3px solid";
    }
}

function _hover_unhighlight(event) {
    if (!base_on)
	return;

    var seq = this.className.replace(/seq/, "");
    var words = document.getElementsByClassName("seq" + seq);
    for (var w = 0; w < words.length; w++) {
	words[w].style.borderBottom = "none";
    }
}

function _toggle_highlighting(event) {
    var tokens = document.getElementsByTagName("span");
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

function _toggle_base(event) {
    var head = document.getElementById("variant_head");
    var text_elem = document.getElementById("text");
    var base_elem = document.getElementById("base_text");
    var base_cb = document.getElementById("base_cb");

    if (base_on) {
	head.style.maxWidth = old_width;
	text_elem.style.width = "99%";
	base_elem.removeAttribute("style");
	var node = document.getElementById("base_text");
	while (node.lastChild) {
	    node.removeChild(node.lastChild);
	}
	base_cb.removeAttribute("checked");
    } else {
	var loader = document.createElement("div");
	loader.className = "loader";
	base_elem.appendChild(loader);

	old_width = head.style.maxWidth;
	head.style.maxWidth = "85%";
	text_elem.style.cssFloat = "left";
	text_elem.style.width = "48%";
	base_elem.style.width = "48%";
	base_cb.checked = "checked";
	get(_display_base, base_url);
    }
    base_on = !base_on;
}

function _display_base(responseText) {
    var base_json = JSON.parse(responseText);
    _content_in_elem("base_text", base_json);
}

function _drag_token(event) {
    event.dataTransfer.setData("seq", event.target.text_seq);
    var prev_coll_token_seq = event.target.className.replace(/seq/, "")
    event.dataTransfer.setData("prev_coll_token_seq", prev_coll_token_seq);
    event.dataTransfer.setData("token_elem", this);
}

function _drag_over_token(event) {
    event.preventDefault();
    this.style.backgroundColor = "#ADDF26";
}

function _drag_leave_token(event) {
    event.preventDefault();
    this.style.backgroundColor = "#fff";
}

function _drop_token(event) {
    event.preventDefault();
    var seq = event.dataTransfer.getData("seq");
    var text_elem = document.getElementById("textSeq" + seq);
    var words = document.getElementsByClassName("seq" + event.dataTransfer.getData("prev_coll_token_seq"));
    for (var w = 0; w < words.length; w++) {
	words[w].style.borderBottom = "none";
    }
    
    var coll_token_seq = this.className.replace(/seq/, "");
    /* Update display. */
    text_elem.className = "seq" + coll_token_seq;
    /* Update changes in database. */
    
    var csrftoken = Cookies.get("csrftoken");
    var data = Object();
    data.seq = seq;
    data.coll_token_seq = coll_token_seq;
    post(data, csrftoken, function() {}, manual_coll_url)

    this.style.backgroundColor = "#fff";
}


