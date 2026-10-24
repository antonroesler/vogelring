/* Sortable table (interactive mode only). */
(function () {
  var table = document.getElementById('table');
  if (!window.__RENDER__ && table) {
    var ths = table.querySelectorAll('thead th[data-col]');
    ths.forEach(function (th) {
      th.classList.add('sortable');
      th.addEventListener('click', function () {
        var col = +th.getAttribute('data-col'), numeric = th.getAttribute('data-numeric') === 'true';
        var asc = th.classList.contains('asc');
        ths.forEach(function (o) { o.classList.remove('asc', 'desc'); });
        th.classList.add(asc ? 'desc' : 'asc');
        var rows = Array.prototype.slice.call(table.tBodies[0].rows);
        var rn = table.querySelector('thead th.rn') ? 1 : 0;
        rows.sort(function (a, b) {
          var ca = a.cells[col + rn], cb = b.cells[col + rn];
          var va = ca.getAttribute('data-value'), vb = cb.getAttribute('data-value');
          var x, y;
          if (numeric) { x = va === null ? -Infinity : parseFloat(va); y = vb === null ? -Infinity : parseFloat(vb); }
          else { x = (va !== null ? va : ca.textContent).trim().toLowerCase(); y = (vb !== null ? vb : cb.textContent).trim().toLowerCase(); }
          if (x < y) return asc ? 1 : -1; if (x > y) return asc ? -1 : 1; return 0;
        });
        rows.forEach(function (r, i) { table.tBodies[0].appendChild(r); if (rn) r.cells[0].textContent = i + 1; });
      });
    });
  }
  window.__READY__ = true;
})();
