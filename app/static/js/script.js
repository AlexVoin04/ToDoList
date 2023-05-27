function importData() {
  // Получаем данные выбранного файла
  var file = document.getElementById('file-input').files[0];
  var reader = new FileReader();
  reader.onload = function(event) {
    var data = JSON.parse(event.target.result);
    // Отправляем данные на сервер
    sendDataToServer(data);
  }
  reader.readAsText(file);
}

function sendDataToServer(data) {
  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/import', true);
  xhr.setRequestHeader('Content-Type', 'application/json');
  xhr.onreadystatechange = function() {
    if (xhr.readyState == 4 && xhr.status == 200) {
      var response = JSON.parse(xhr.responseText);
      if (response.success) {
        // Обновляем таблицу с импортированными данными
        update