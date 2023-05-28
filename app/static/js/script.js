$(function() {
  $("#header-placeholder").load("{{ url_for('static', filename='html/header.html') }}");
  $("#footer-placeholder").load("{{ url_for('static', filename='html/footer.html') }}");
});

$(document).ready(function() {
   $("#import-form").submit(function(event) {
      event.preventDefault();
      var formData = new FormData($(this)[0]);
      $.ajax({
         url: "/import",
         type: "POST",
         data: formData,
         contentType: false,
         processData: false,
         success: function(response) {
           alert("Imported successfully");
         },
         error: function(xhr, status, error) {
           alert("Error importing: " + error);
         }
      });
   });
});


