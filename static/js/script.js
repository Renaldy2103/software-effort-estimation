document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
        const message = form.getAttribute("data-confirm") || "Lanjutkan?";
        if (!window.confirm(message)) {
            event.preventDefault();
        }
    });
});

document.querySelectorAll('input[type="number"]').forEach((input) => {
    input.addEventListener("input", () => {
        const value = input.value.trim();
        if (value === "") {
            input.setCustomValidity("");
            return;
        }
        const number = Number(value);
        if (!Number.isFinite(number)) {
            input.setCustomValidity("Masukkan angka yang valid.");
        } else {
            input.setCustomValidity("");
        }
    });
});
