async function loadFindings() {
  const response = await fetch('findings.json');
  if (!response.ok) {
    throw new Error('Unable to load findings.json');
  }
  return await response.json();
}

function populateOptions(select, values) {
  select.innerHTML = '';
  const allOption = document.createElement('option');
  allOption.value = '';
  allOption.textContent = 'All';
  select.appendChild(allOption);
  values.sort().forEach((value) => {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });
}

function renderMeta(meta) {
  const container = document.getElementById('meta');
  container.textContent = `Run ${meta.run_id} · Model ${meta.model} · Tokens ${meta.tokens} · Cost $${meta.cost_usd}`;
}

function renderReview(review) {
  document.getElementById('review-summary').textContent = review.summary || '';
  const strengths = document.getElementById('review-strengths');
  strengths.innerHTML = '';
  (review.strengths || []).forEach((item) => {
    const li = document.createElement('li');
    li.textContent = item;
    strengths.appendChild(li);
  });
  const weaknesses = document.getElementById('review-weaknesses');
  weaknesses.innerHTML = '';
  (review.weaknesses || []).forEach((item) => {
    const li = document.createElement('li');
    li.textContent = item;
    weaknesses.appendChild(li);
  });
  const fixes = document.getElementById('review-fixes');
  fixes.innerHTML = '';
  (review.top_fixes || []).forEach((fix) => {
    const li = document.createElement('li');
    li.textContent = `${fix.section}: ${fix.action} (${fix.impact})`;
    fixes.appendChild(li);
  });
  const missing = document.getElementById('review-missing');
  missing.innerHTML = '';
  (review.missing_refs || []).forEach((item) => {
    const li = document.createElement('li');
    li.textContent = item;
    missing.appendChild(li);
  });
}

function renderTable(issues) {
  const tbody = document.querySelector('#issues-table tbody');
  tbody.innerHTML = '';
  issues.forEach((issue) => {
    const row = document.createElement('tr');
    row.dataset.issueId = issue.id;
    row.innerHTML = `
      <td>${issue.id}</td>
      <td>${issue.phase}</td>
      <td>${issue.type}</td>
      <td>${issue.severity}</td>
      <td>${issue.span.file}</td>
      <td>${issue.span.line}</td>
    `;
    row.addEventListener('click', () => showDetails(issue));
    tbody.appendChild(row);
  });
}

function showDetails(issue) {
  document.getElementById('excerpt').textContent = issue.excerpt || '';
  document.getElementById('suggestion').textContent = issue.suggestion || '';
  document.getElementById('explanation').textContent = issue.explanation || '';
}

function applyFilters(issues) {
  const phase = document.getElementById('filter-phase').value;
  const type = document.getElementById('filter-type').value;
  const severity = document.getElementById('filter-severity').value;
  const file = document.getElementById('filter-file').value;
  return issues.filter((issue) => {
    if (phase && issue.phase !== phase) return false;
    if (type && issue.type !== type) return false;
    if (severity && issue.severity !== severity) return false;
    if (file && issue.span.file !== file) return false;
    return true;
  });
}

function setupFilters(issues) {
  const phaseSelect = document.getElementById('filter-phase');
  const typeSelect = document.getElementById('filter-type');
  const severitySelect = document.getElementById('filter-severity');
  const fileSelect = document.getElementById('filter-file');
  populateOptions(phaseSelect, Array.from(new Set(issues.map((i) => i.phase))));
  populateOptions(typeSelect, Array.from(new Set(issues.map((i) => i.type))));
  populateOptions(severitySelect, Array.from(new Set(issues.map((i) => i.severity))));
  populateOptions(fileSelect, Array.from(new Set(issues.map((i) => i.span.file))));
  [phaseSelect, typeSelect, severitySelect, fileSelect].forEach((select) => {
    select.addEventListener('change', () => {
      const filtered = applyFilters(issues);
      renderTable(filtered);
    });
  });
}

async function init() {
  try {
    const data = await loadFindings();
    const issues = data.issues || [];
    renderMeta(data.meta || {});
    renderReview(data.review || {});
    renderTable(issues);
    setupFilters(issues);
  } catch (error) {
    const meta = document.getElementById('meta');
    meta.textContent = error.message;
  }
}

document.addEventListener('DOMContentLoaded', init);
