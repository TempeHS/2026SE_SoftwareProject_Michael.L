(function () {
  document.querySelectorAll(".role-form").forEach(function (form) {
    var select = form.querySelector(".role-select");
    var custom = form.querySelector(".role-custom");
    if (!select || !custom) return;

    function sync() {
      if (select.value === "__custom__") {
        custom.style.display = "";
        custom.required = true;
        if (!custom.value) custom.focus();
      } else {
        custom.style.display = "none";
        custom.required = false;
        custom.value = select.value; // hidden input carries the chosen preset
      }
    }

    // Initialise hidden value for preset selections
    if (select.value !== "__custom__") {
      custom.value = select.value;
    }

    select.addEventListener("change", sync);

    form.addEventListener("submit", function () {
      // Ensure the `role` input always carries the right value
      if (select.value !== "__custom__") {
        custom.value = select.value;
      }
    });
  });
})();