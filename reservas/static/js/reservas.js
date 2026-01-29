function seleccionarMesa(id) {
    document.getElementById('mesa_id').value = id;

    document.querySelectorAll('.mesa').forEach(m => {
        m.style.border = '1px solid gray';
    });

    event.target.style.border = '3px solid green';
}