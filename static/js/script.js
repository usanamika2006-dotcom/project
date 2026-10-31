document.addEventListener('DOMContentLoaded', () => {
  const menuToggle = document.querySelector('#menuToggle');
  const sidebar = document.querySelector('#sidebar');
  menuToggle?.addEventListener('click', () => sidebar?.classList.toggle('open'));
  document.addEventListener('click', (event) => {
    if (sidebar?.classList.contains('open') && !sidebar.contains(event.target) && !menuToggle?.contains(event.target)) sidebar.classList.remove('open');
  });
  document.querySelectorAll('.flash-close').forEach((button) => button.addEventListener('click', () => button.closest('.flash')?.remove()));
  document.querySelectorAll('.table-search').forEach((input) => input.addEventListener('input', () => {
    const table = input.closest('.panel')?.querySelector('tbody');
    const term = input.value.toLocaleLowerCase();
    table?.querySelectorAll('tr').forEach((row) => { row.hidden = !row.innerText.toLocaleLowerCase().includes(term); });
  }));
});
