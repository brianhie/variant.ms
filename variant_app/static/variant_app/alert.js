/**
 * @version 1.0.0.1
 * @author smile
 * @email 1060656096@qq.com
 *
 * Usage:
 * var options = {
 *     delay: 1000,
 *     cancel: true,
 *     cancelText: 'Cancel',
 *     cancelColor: 'red',
 *     cancelCallBack: function(event) {
 *         console.log('cancel');
 *     },
 *     confirm: true,
 *     confirmText: 'Ok',
 *     confirmColor: 'black',
 *     confirmCallBack: function(event) {
 *         console.log('confirm');
 *     }
 * }
 */

window.alert = function(title, message, options) {
    if (typeof(options) != 'object') {
	options = {};
    }
    if (options.delay == undefined) {
	options.delay = 0;
    } else {
	options.delay++;
	options.delay--;
    }

    setTimeout(function() {
	if (!window.smile_alert) {
	    // Initialize config.
	    var smile_obj={
		selecter: 'smile-alert',
		element : null,
		filter: 30,
		cancelElement: null,
		confirmElement: null

	    };
	    smile_obj.element = document.querySelector(smile_obj.selecter);

	} else {
	    // Clear style.
	    if (window.smile_alert.cancel) {
		window.smile_alert.cancelElement.style  = '';
	    }
	    if (window.smile_alert.confirm) {
		window.smile_alert.confirmElement.style  = '';
	    }
	    // Show alert.
	    window.smile_alert.element.style.display = "block";

	    smile_obj = window.smile_alert;
	}
	// Default options for cancel button.
	smile_obj.cancel = (options.cancel != undefined) ? options.cancel : false;
	smile_obj.cancelText= (options.cancelText != undefined) ? options.cancelText : 'Cancel';
	smile_obj.cancelColor = (options.cancelColor != undefined) ? options.cancelColor : '#000';
	smile_obj.cancelCallBack = function(event) {
	    window.smile_alert.cancelElement.style = "background-color:#999;color:#000;filter:alpha(opacity="+(window.smile_alert.filter)+");-moz-opacity:"+(window.smile_alert.filter/100)+";-khtml-opacity: "+(window.smile_alert.filter/100)+";opacity: "+(window.smile_alert.filter/100)+";";
	    setTimeout(function() {
		window.smile_alert.element.style.display = "none";
		// Execute user provided call back.
		if(typeof(options.cancelCallBack) == 'function') {
		    options.cancelCallBack(event);
		}
		return true;
	    }, window.smile_alert.delay);
	};

	// Default options for confirm button.
	smile_obj.message = message ? message : "";
	smile_obj.title = title ? title : "";
	smile_obj.confirm  = options.confirm  != undefined ? options.confirm  : true;
	smile_obj.confirmText = options.confirmText != undefined ? options.confirmText : 'Ok';
	smile_obj.confirmColor = (options.confirmColor != undefined) ? options.confirmColor : '#000';
	smile_obj.confirmCallBack = function(event) {
	    window.smile_alert.confirmElement.style = "background-color:#999;color:#222;filter:alpha(opacity="+(window.smile_alert.filter)+");-moz-opacity:"+(window.smile_alert.filter/100)+";-khtml-opacity: "+(window.smile_alert.filter/100)+";opacity: "+(window.smile_alert.filter/100)+";";
	    setTimeout(function() {
		window.smile_alert.element.style.display = "none";
		if (typeof(options.confirmCallBack) == 'function') {
		    options.confirmCallBack(event);
		}
		return true;
	    }, window.smile_alert.delay);
	};

	if (!smile_obj.element) {
	    smile_obj.html =
		'<div class="'+smile_obj.selecter+'" id="'+smile_obj.selecter+'">' +
		'<div class="'+smile_obj.selecter+'-mask"></div>' +
		'<div class="'+smile_obj.selecter+'-message-body">' +
		'<div class="'+smile_obj.selecter+'-message-tbf '+smile_obj.selecter+'-message-title"><strong class="'+smile_obj.selecter+'-message-tbf ">'+smile_obj.title+'</strong></div>' +
		'<div class="'+smile_obj.selecter+'-message-tbf '+smile_obj.selecter+'-message-content">'+smile_obj.message+'</div>' +
		'<div class="'+smile_obj.selecter+'-message-tbf '+smile_obj.selecter+'-message-button">';

	    if (smile_obj.cancel || true) {
		smile_obj.html += '<a href="javascript:;" class="'+smile_obj.selecter+'-message-tbf '+smile_obj.selecter+'-message-button-cancel">'+smile_obj.cancelText+'</a>';
	    }

	    if (smile_obj.confirm || true) {
		smile_obj.html += '<a href="javascript:;" class="'+smile_obj.selecter+'-message-tbf '+smile_obj.selecter+'-message-button-confirm">'+smile_obj.confirmText+'</a>';
	    }

	    smile_obj.html +=
	    '</div>'
		+    '</div>'
		+'</div>';
	    //document create element
	    element = document.createElement('div');
	    element.className = "sans_font";
	    element.id= smile_obj.selecter+'-wrap';
	    element.innerHTML = smile_obj.html;
	    document.body.appendChild(element );
	    //smile alert element
	    smile_obj.element = document.querySelector('.'+smile_obj.selecter);
	    smile_obj.cancelElement = document.querySelector('.'+smile_obj.selecter+'-message-button-cancel');

	    // Cancel button callback.
	    if (smile_obj.cancel) {
		document.querySelector('.'+smile_obj.selecter+'-message-button-cancel').style.display = 'block';
	    } else {
		document.querySelector('.'+smile_obj.selecter+'-message-button-cancel').style.display = 'none';
	    }

	    // Confirm button callback.
	    smile_obj.confirmElement = document.querySelector('.'+smile_obj.selecter+'-message-button-confirm');
	    if (smile_obj.confirm ){
		document.querySelector('.'+smile_obj.selecter+'-message-button-confirm').style.display ='block';
	    } else {
		document.querySelector('.'+smile_obj.selecter+'-message-button-confirm').style.display = 'none';
	    }

	    smile_obj.cancelElement.onclick = smile_obj.cancelCallBack;
	    smile_obj.confirmElement.onclick = smile_obj.confirmCallBack;
	    window.smile_alert = smile_obj;
	}

	// Cancel button.
	smile_obj.cancelElement = document.querySelector('.'+smile_obj.selecter+'-message-button-cancel');
	smile_obj.cancelElement.innerHTML =  smile_obj.cancelText;
	smile_obj.cancelElement.style.color =  smile_obj.cancelColor;
	if (smile_obj.cancel) {
	    smile_obj.cancelElement.style.display = 'block';
	} else {
	    smile_obj.cancelElement.style.display = 'none';
	}

	// Confirm button.
	smile_obj.confirmElement = document.querySelector('.'+smile_obj.selecter+'-message-button-confirm');
	smile_obj.confirmElement.innerHTML = smile_obj.confirmText;
	smile_obj.confirmElement.style.color =  smile_obj.confirmColor;
	if (smile_obj.confirm) {
	    smile_obj.confirmElement.style.display = 'block';
	} else {
	    smile_obj.confirmElement.style.display = 'none';
	}

	smile_obj.cancelElement.onclick  = smile_obj.cancelCallBack;
	smile_obj.confirmElement.onclick  = smile_obj.confirmCallBack;

	// Title and message.
	if (smile_obj.title && smile_obj.message) {
	    document.querySelector('.'+smile_obj.selecter+'-message-title').innerHTML = smile_obj.title
	    document.querySelector('.'+smile_obj.selecter+'-message-content').innerHTML = smile_obj.message;
	} else if (smile_obj.message) {
	    document.querySelector('.'+smile_obj.selecter+'-message-content').innerHTML = smile_obj.message;
	} else if (smile_obj.title) {
	    document.querySelector('.'+smile_obj.selecter+'-message-title').innerHTML = smile_obj.title;
	}

	window.smile_alert = smile_obj;
    }, options.delay);
};
