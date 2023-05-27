// get all checkboxes
 var checkboxes = document.getElementsByName('check_box');

// add click event listener to the check-all button
document.getElementById('check-all').addEventListener('click', function() {
  checkboxes.forEach(function(checkbox) {
    checkbox.checked = !checkbox.checked;
  });
});