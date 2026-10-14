const views = [...document.querySelectorAll('[data-view]')];
const navItems = [...document.querySelectorAll('[data-view-target]')];
const toast = document.querySelector('[data-toast]');
const toastMessage = document.querySelector('[data-toast-message]');
let toastTimer;

const nodeDetails = {
  ISP: { description: 'Simulated WAN edge · three design links', role: 'WAN edge' },
  'HQ-R1': { description: 'HQ router · two design tunnels', role: 'Edge router' },
  'BR1-R1': { description: 'Branch 1 router · corrected design', role: 'Edge router' },
  'BR2-R1': { description: 'Branch 2 router · corrected design', role: 'Edge router' },
  'HQ-SW1': { description: 'HQ access layer · VLANs 10 / 20 / 30 / 99', role: 'Access switch' },
  'BR1-SW1': { description: 'Branch 1 access layer · management SVI corrected', role: 'Access switch' },
  'BR2-SW1': { description: 'Branch 2 access layer · trunk policy corrected', role: 'Access switch' }
};

function showToast(message) {
  clearTimeout(toastTimer);
  toastMessage.textContent = message;
  toast.classList.add('is-visible');
  toastTimer = setTimeout(() => toast.classList.remove('is-visible'), 3000);
}

function activateView(target) {
  const nextView = document.querySelector(`[data-view="${target}"]`);
  if (!nextView) return;
  views.forEach((view) => view.classList.toggle('is-visible', view === nextView));
  document.querySelectorAll('.top-nav-item').forEach((item) => item.classList.toggle('is-active', item.dataset.viewTarget === target));
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function setScenario(scenario) {
  const result = document.querySelector('[data-scenario-result]');
  const chip = document.querySelector('[data-scenario-chip]');
  const title = document.querySelector('[data-result-title]');
  const copy = document.querySelector('[data-result-copy]');
  const code = document.querySelector('[data-result-code]');
  const explanation = document.querySelector('.decision-explanation p');
  document.querySelectorAll('[data-scenario]').forEach((card) => card.classList.toggle('is-selected', card.dataset.scenario === scenario));

  if (scenario === 'unsafe') {
    result.classList.add('is-danger');
    result.querySelector('.result-mark').textContent = '!';
    chip.textContent = 'CHANGE BLOCKED';
    chip.style.color = 'var(--red)';
    chip.style.borderColor = 'rgba(255,143,143,.3)';
    chip.style.background = 'var(--red-dim)';
    title.textContent = 'Unsafe change blocked';
    copy.textContent = 'Guest traffic now has a successful path to the HQ server. The merge gate must stop this change.';
    code.textContent = 'EXIT 1';
    explanation.textContent = 'The new rule opens a path from Guest to the private server. The change is blocked before review.';
    showToast('Unsafe change blocked');
  } else {
    result.classList.remove('is-danger');
    result.querySelector('.result-mark').textContent = '✓';
    chip.textContent = 'SAFE CHANGE';
    chip.style.color = '';
    chip.style.borderColor = '';
    chip.style.background = '';
    title.textContent = 'Safe change passed';
    copy.textContent = 'All required policy assertions are satisfied. The change can proceed to human review.';
    code.textContent = 'EXIT 0';
    explanation.textContent = 'The safe change keeps private networks protected before allowing public services.';
    showToast('Safe change passed');
  }
}

function openNodeModal(node) {
  const detail = nodeDetails[node] || nodeDetails['HQ-R1'];
  document.querySelector('#detail-modal-title').textContent = node;
  document.querySelector('[data-modal-description]').textContent = detail.description;
  document.querySelector('[data-modal-role]').textContent = detail.role;
  document.querySelector('[data-modal-backdrop]');
  const backdrop = document.querySelector('[data-modal-backdrop]');
  backdrop.classList.add('is-visible');
  backdrop.setAttribute('aria-hidden', 'false');
}

function closeModal() {
  const backdrop = document.querySelector('[data-modal-backdrop]');
  backdrop.classList.remove('is-visible');
  backdrop.setAttribute('aria-hidden', 'true');
}

navItems.forEach((item) => item.addEventListener('click', () => activateView(item.dataset.viewTarget)));
document.querySelectorAll('[data-action="run-safe"]').forEach((button) => button.addEventListener('click', () => {
  activateView('simulate');
  setScenario('safe');
}));
document.querySelector('[data-action="view-evidence"]')?.addEventListener('click', () => activateView('evidence'));
document.querySelector('[data-action="run-policy"]')?.addEventListener('click', () => showToast('Policy gate passed · 4 checks complete'));
document.querySelector('[data-action="copy-summary"]')?.addEventListener('click', async () => {
  const summary = 'P3 Network Assurance: 16 checks passed. Staff access allowed, Guest access blocked, unsafe change stopped. Live deployment not executed.';
  try { await navigator.clipboard.writeText(summary); showToast('Executive summary copied'); } catch { showToast('Summary ready: 16 checks passed'); }
});
document.querySelectorAll('[data-scenario]').forEach((card) => card.addEventListener('click', () => setScenario(card.dataset.scenario)));
document.querySelectorAll('[data-node]').forEach((node) => node.addEventListener('click', () => openNodeModal(node.dataset.node)));
document.querySelector('[data-modal-close]')?.addEventListener('click', closeModal);
document.querySelector('[data-modal-backdrop]')?.addEventListener('click', (event) => { if (event.target === event.currentTarget) closeModal(); });
document.addEventListener('keydown', (event) => { if (event.key === 'Escape') closeModal(); });
document.querySelectorAll('[data-finding]').forEach((finding) => finding.addEventListener('click', () => showToast(`${finding.dataset.finding} · desired state recorded`)));
document.querySelector('[data-action="presentation"]')?.addEventListener('click', () => {
  document.body.classList.toggle('presentation-mode');
  showToast(document.body.classList.contains('presentation-mode') ? 'Presentation mode enabled' : 'Presentation mode disabled');
});
