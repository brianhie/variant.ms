function dropdown() {
    document.getElementById("myDropdown").classList.toggle("show");
}

function delete_corpus(delete_url) {
    var options = {
	cancel: true,
	cancelText: 'Cancel',
	confirmText: 'Delete',
	confirmColor: 'red',
	confirmCallBack: function() {
	    window.location.replace(delete_url);
	},
    }
    alert("Are you sure you want to delete this text?",
	  "You'll permanently lose all of its variant and collation data.",
	  options);
}

function delete_text(delete_url) {
    var options = {
	cancel: true,
	cancelText: 'Cancel',
	confirmText: 'Delete',
	confirmColor: 'red',
	confirmCallBack: function() {
	    window.location.replace(delete_url);
	},
    }
    alert("Are you sure you want to delete this variant?",
	  "You'll permanently lose all of its collation data.",
	  options);
}

// Close the dropdown menu if the user clicks outside of it
window.onclick = function(event) {
  if (!event.target.matches('.dropbtn')) {

    var dropdowns = document.getElementsByClassName("dropdown-content");
    var i;
    for (i = 0; i < dropdowns.length; i++) {
      var openDropdown = dropdowns[i];
      if (openDropdown.classList.contains('show')) {
        openDropdown.classList.remove('show');
      }
    }
  }
}
