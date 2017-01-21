_width_resize = function(event) {
    var w = window,
    d = document,
    e = d.documentElement,
    g = d.getElementsByTagName('body')[0],
    x = w.innerWidth || e.clientWidth || g.clientWidth;

    var small = false, medium = false, large = false;
    var head = document.getElementById("variant_head");
    if (head) {
	if (x < 1500 && !small) {
	    head.style.maxWidth = "85%";
	    small = true;
	    medium = false;
	    large = false;
	} else if (x < 1800 && !medium) {
	    head.style.maxWidth = "70%";
	    small = false;
	    medium = true;
	    large = false;
	} else if (!large) {
	    head.style.maxWidth = "60%";
	    small = false;
	    medium = false;
	    large = true;
	}
    }
};

document.addEventListener("DOMContentLoaded", function() {
    _width_resize();
});

window.addEventListener("resize", _width_resize);


