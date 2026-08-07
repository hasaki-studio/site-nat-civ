// Bascule des blocs repliables (aria-expanded / aria-controls).
(function () {
  function setupToggle(button) {
    if (!button) return;
    var controls = button.getAttribute('aria-controls');
    var target = controls ? document.getElementById(controls) : null;
    if (!target) return;
    button.addEventListener('click', function () {
      var expanded = button.getAttribute('aria-expanded') === 'true';
      button.setAttribute('aria-expanded', String(!expanded));
      if (expanded) {
        target.setAttribute('hidden', '');
      } else {
        target.removeAttribute('hidden');
      }
    });
  }
  document.querySelectorAll('[aria-controls]').forEach(setupToggle);
})();
