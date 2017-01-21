document.addEventListener("DOMContentLoaded", function() {
    var elems = document.getElementsByClassName("formattedDate");
    for (var e = 0; e < elems.length; e++) {
	var elem = elems[e];
	elem.onkeyup = _format_year;
    }
});

_format_year = function(event) {
    if (!this.value)
	return;

    var key = event.keyCode || event.charCode;
    // Let user type backspace, delete, or dash, respectively.
    if (key == 8 || key == 46 || key == 189)
        return;

    var s = this.value.replace(/\D/g, '');

    if (s.length > 8) { // 8 is number of digits in YYYY-MM-DDD
	s = s.substr(0, 8);
    }
    var new_value = s.substr(0, 4);
    if (s.length > 4) {
	new_value += "-" + s.substr(4, 2);
	if (s.length > 6) {
	    new_value += "-" + s.substr(6, 2);
	}
    }
    this.value = new_value;
}

