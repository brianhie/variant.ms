function dropdown() {
    document.getElementById("myDropdown").classList.toggle("show");
}

function delete_corpus(delete_url) {
    var ok = confirm("Are you sure you want to delete this text?  You'll lose all of its variant and collation data.");
    if (ok == true) {
	window.location.replace(delete_url);
    }
}

function delete_text(delete_url) {
    console.log(delete_url);
    var ok = confirm("Are you sure you want to delete this variant?  You'll lose all collation data associated with it.");
    if (ok == true) {
	window.location.replace(delete_url);
    }
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
