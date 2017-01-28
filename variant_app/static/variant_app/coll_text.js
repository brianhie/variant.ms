var corpus_id = "";
var tokens_url = "";
var post_word_url = "";
var favorite_url = "";
var last_event = null;
var highlight_on = true;
var variant_texts = null;
var selected = null;
var a_block = null;

function coll_text_visualization(text_url, t_url, pw_url, f_url, cid) {
    corpus_id = cid;
    tokens_url = _base_tokens_url(t_url);
    post_word_url = pw_url;
    favorite_url = f_url;

    a_block = document.createElement("div");
    a_block.style.overflowY = "auto";
    a_block.style.maxHeight = "500px";
    a_block.style.position = "relative";

    document.addEventListener("DOMContentLoaded", function() {
	var checkbox = document.getElementById("cb");
	if (checkbox) {
	    checkbox.onclick = _toggle_highlighting;
	}

	var annotation = document.getElementById("annotation");
	if (annotation) {
	    variant_texts = annotation.childNodes[1];
	    annotation.innerHTML = "";
	}
	document.body.onclick = _variant_texts_side;

	var favorite = document.getElementById("fav");
	if (favorite) {
	    favorite.onclick = _post_favorite;
	}

	get(_display_content, text_url);
    });
}

function _base_tokens_url(t_url) {
    var arr = t_url.replace(/\/$/g, '').split('/');
    arr.pop();
    arr.pop();
    arr.pop();
    return arr.join('/');
}

function _var_color(variability) {
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

    var min_len = 10;
    var max_len = 30;

    var tokens = [];
    for (var t = 0; t < content_json.tokens.length; t++) {
	var seq = content_json.tokens[t].seq;
	var word = content_json.tokens[t].word;
	var variability = parseFloat(content_json.tokens[t].variability);
	var is_hidden = content_json.tokens[t].is_hidden;

	var token = document.createElement("span");
	token.id = "seq" + seq
	token.className = "coll_token"
	if (word.replace(/\s+/g,'') != "") {
	    token.style.backgroundColor = _var_color(variability);
	}
	token.prev_color = token.style.backgroundColor;
	if (is_hidden) {
	    token.style.color = token.prev_color;
	}
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
    var coll_token_seq = content_json.coll_token_seq;

    var sequence_list = document.createElement("table");
    sequence_list.className = "annotate_block"
    sequence_list.onclick = function(event) { event.stopPropagation(); }

    for (var s = 0; s < content_json.sequences.length; s++) {
	var sequence = content_json.sequences[s];
	var sequence_row = document.createElement("tr")
	sequence_row.className = "annotate_row"

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
	sequence_elem.onclick = post_word_change;
	sequence_elem.post_word_data = {
	    "coll_token_seq": coll_token_seq,
	    "corpus_id": corpus_id,
	    "text_name": sequence.text_name,
	};

	for (var t = 0; t < sequence.tokens.length; t++) {
	    var token = sequence.tokens[t];
	    var span = document.createElement("span");
	    span.textContent = token.word
	    if (token.is_center) {
		span.style.fontWeight = "bold";
		if (sequence_elem.post_word_data.word) {
		    sequence_elem.post_word_data.word += token.word;
		} else {
		    sequence_elem.post_word_data.word = token.word;
		}
		if (token.is_coll) {
		    sequence_elem.style.outline = "#444 1px solid";
		}
	    }
	    sequence_elem.appendChild(span);
	}
	sequence_row.appendChild(sequence_elem);
	sequence_list.appendChild(sequence_row);
    }

    a_block.innerHTML = "";
    a_block.appendChild(sequence_list);

    var annotation = document.getElementById("annotation");
    annotation.innerHTML = "";
    annotation.appendChild(a_block);

    /* Logic for computing offset. */
    var a = document.getElementById("annotation");
    var c = document.getElementById("contain");
    var top =  window.pageYOffset + last_event.clientY - a.offsetTop;
    var height = a_block.clientHeight;
    if (top + height > c.clientHeight - 150) { // Why 150? It's magic!
	a_block.style.top = Math.max(c.clientHeight - height - 150, 0) + "px";
    } else {
	a_block.style.top = Math.max(top - (height/3), 0) + "px";
    }
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

    var loader = document.createElement("div");
    loader.style.position = "absolute";
    loader.style.top = window.pageYOffset + last_event.clientY - 20 + "px";
    loader.className = "loader";
    var annotation = document.getElementById("annotation");
    annotation.innerHTML = "";
    annotation.appendChild(loader);

    event.stopPropagation();

    get(_display_tokens, url);
}

function _toggle_highlighting(event) {
    var tokens = document.getElementsByClassName("coll_token");
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

function post_word_change(event) {
    if (this.post_word_data) {
	var csrftoken = Cookies.get("csrftoken");
	post(this.post_word_data, csrftoken, function() {}, post_word_url)
	var seq = this.post_word_data.coll_token_seq;

	var token = document.getElementById("seq" + seq);
	if (this.post_word_data.word) {
	    document.getElementById("seq" + seq).textContent = this.post_word_data.word;
	    token.style.removeProperty("color");
	} else {
	    token.style.color = token.prev_color;
	}

	/* Only highlight clicked word. */
	var to_highlight = this;
	var node = to_highlight.parentNode.parentNode.firstChild;
	while (node) {
	    if (node.lastChild == to_highlight) {
		node.lastChild.style.outline = "#444 1px solid";
	    } else {
		node.lastChild.removeAttribute("style");
	    }
	    node = node.nextSibling;
	}
    }
    event.stopPropagation();
}

function _post_favorite(event) {
    var csrftoken = Cookies.get("csrftoken");
    post({}, csrftoken, function() {}, favorite_url)

    if (this.style.color) {
	this.removeAttribute("style");
	this.innerHTML = "&#9733; Add to favorites";
    } else {
	this.style.color = "#d5a01b";
	this.innerHTML = "&#9733; Favorited";
    }
}
