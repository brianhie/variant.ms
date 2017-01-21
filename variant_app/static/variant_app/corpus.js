var is_public_url = "";
var is_public = true;
var pub_cb = null;

corpus_visualization = function(pub_url, is_p) {
    is_public_url = pub_url;
    is_public = is_p == "True";

    document.addEventListener("DOMContentLoaded", function() {
	pub_cb = document.getElementById("pub_cb");
	if (pub_cb) {
	    pub_cb.onclick = _toggle_public;
	    if (is_public) {
		_pub_cb_check();
	    } else {
		_pub_cb_uncheck();
	    }
	}
    });
}

_toggle_public = function() {
    var conf_msg = "";
    if (is_public) {
	conf_msg = "Are you sure you want to make this text private? Users who have favorited your text will no longer be able to see it.";
    } else {
	conf_msg = "Users who search for this text will be now be able to see it!"
    }
    var ok = confirm(conf_msg);
    if (ok) {
	var csrftoken = Cookies.get("csrftoken");
	post({}, csrftoken, function() {}, is_public_url)
	is_public = !is_public;
	if (is_public) {
	    _pub_cb_check();
	} else {
	    _pub_cb_uncheck();
	}
    }
}

_pub_cb_check = function() {
    if (pub_cb) {
	pub_cb.checked = "checked";
    }
}

_pub_cb_uncheck = function() {
    if (pub_cb) {
	pub_cb.removeAttribute("checked");
    }
}
