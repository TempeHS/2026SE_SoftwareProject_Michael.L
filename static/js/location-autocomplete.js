(function () {
  "use strict";

  const input = document.getElementById("location");
  if (!input) return;

  // Build dropdown
  const wrapper = document.createElement("div");
  wrapper.style.position = "relative";
  input.parentNode.insertBefore(wrapper, input);
  wrapper.appendChild(input);

  const dropdown = document.createElement("ul");
  dropdown.className = "list-group position-absolute w-100 shadow-sm";
  dropdown.style.zIndex = "1000";
  dropdown.style.maxHeight = "240px";
  dropdown.style.overflowY = "auto";
  dropdown.style.display = "none";
  wrapper.appendChild(dropdown);

  let debounceTimer = null;

  async function fetchSuggestions(query) {
    const url =
      "https://nominatim.openstreetmap.org/search?q=" +
      encodeURIComponent(query) +
      "&format=json&limit=5&addressdetails=1";
    const res = await fetch(url, { headers: { Accept: "application/json" } });
    if (!res.ok) return [];
    return await res.json();
  }

  function renderSuggestions(items) {
    dropdown.innerHTML = "";
    if (!items.length) {
      dropdown.style.display = "none";
      return;
    }
    items.forEach((item) => {
      const li = document.createElement("li");
      li.className = "list-group-item list-group-item-action small";
      li.style.cursor = "pointer";
      li.textContent = item.display_name;
      li.addEventListener("mousedown", function (e) {
        e.preventDefault();
        input.value = item.display_name;
        dropdown.style.display = "none";
      });
      dropdown.appendChild(li);
    });
    dropdown.style.display = "block";
  }

  input.addEventListener("input", function () {
    const q = input.value.trim();
    clearTimeout(debounceTimer);
    if (q.length < 3) {
      dropdown.style.display = "none";
      return;
    }
    debounceTimer = setTimeout(async () => {
      try {
        const items = await fetchSuggestions(q);
        renderSuggestions(items);
      } catch (e) {
        dropdown.style.display = "none";
      }
    }, 350);
  });

  input.addEventListener("blur", function () {
    setTimeout(() => (dropdown.style.display = "none"), 150);
  });
})();
