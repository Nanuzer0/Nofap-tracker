var span = document.getElementById('span');

function time() {
  d = new Date();
  if (d.getHours() == 0 && d.getMinutes() == 0 && d.getSeconds() == 0) {
    location.reload();
    return;
  }
  span.textContent = d.getHours() + ' Hours, '
  + d.getMinutes() + ' Minutes, '
  + d.getSeconds() + ' Seconds ';
}

time();

setInterval(time, 1000);
