/* Navigazione tra report locali già generati. */
(() => {
  'use strict';
  const select = document.getElementById('stage-select');
  const frame = document.getElementById('stage-report');
  const link = document.getElementById('open-report');
  function showStage() {
    frame.setAttribute('src', select.value);
    frame.setAttribute('title', `Report · ${select.options[select.selectedIndex].textContent}`);
    link.setAttribute('href', select.value);
  }
  select.onchange = showStage;
  showStage();
})();
