var corpus_id = "";
var base_url = "";

function text_visualization(text_url, b_url, cid) {
    corpus_id = cid;
    base_url = b_url;
    _get(_display_content, text_url);
}

function _get(func, url) {
    // TODO: Add progess bar or loading icon.

    console.log("here");
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.open("GET", url);
    xmlhttp.onreadystatechange = function()
    {
        if ((xmlhttp.status == 200) && (xmlhttp.readyState == 4))
        {
            func(xmlhttp.responseText);
        }
	else if (xmlhttp.status == 404)
	{
	    alert("Sorry, we couldn't find your text.")
	}
	else if (xmlhttp.status == 500)
	{
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
		    "class=\"seq" + seq + "\">" + word + "</span>");
    }
    text_elem.innerHTML = content;
}

function _display_content(responseText) {
    var content_json = JSON.parse(responseText);
    _content_in_elem("text", content_json);
    _load_base();
}

function _load_base() {
    _get(_display_base, base_url);
}

function _display_base(responseText) {
    var text_elem = document.getElementById("text");
    text_elem.style.cssFloat = "left";
    text_elem.style.paddingLeft = "5%";
    text_elem.style.maxWidth = "40%";

    var base_json = JSON.parse(responseText);
    var base_elem = document.getElementById("base_text");
    base_elem.style.cssFloat = "right";
    _content_in_elem("base_text", base_json);
    base_elem.style.paddingLeft = "3%";
    base_elem.style.marginRight = "8%";
    base_elem.style.maxWidth = "40%";
}

function _hover_highlight(seq) {
    var words = document.getElementsByClassName("seq" + seq);
    for (var w = 0; w < words.length; w++) {
	words[w].style.backgroundColor = "#FFFF00";
    }
}

function _hover_unhighlight(seq) {
    var words = document.getElementsByClassName("seq" + seq);
    for (var w = 0; w < words.length; w++) {
	words[w].style.backgroundColor = "#fff";
    }
}
