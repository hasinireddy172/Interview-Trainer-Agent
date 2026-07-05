/**
 * main.js — AI Interview Trainer
 * IBM Granite · Flask · Bootstrap 5
 *
 * Tab switching uses direct DOM classList manipulation — NOT Bootstrap Tab JS.
 * This eliminates all Bootstrap Tab state-management race conditions.
 *
 * State.store holds generated data per category so tabs switch instantly
 * without re-fetching.
 */

/* ══════════════════════════════════════════════
   GLOBAL STATE
══════════════════════════════════════════════ */
const State = {
  jobRole: '',
  // Stores generated content per category; null = not yet generated
  store: {
    hr:         null,   // array of question objects
    technical:  null,   // array of question objects
    behavioral: null,   // array of question objects
    tips:       null,   // tips object
  },
};

/* ══════════════════════════════════════════════
   DOM REFS
══════════════════════════════════════════════ */
let els = {};

function resolveEls() {
  const g = (x) => document.getElementById(x);
  els = {
    // Resume
    resumeDropZone:  g('resumeDropZone'),
    resumeFile:      g('resumeFile'),
    resumeFileName:  g('resumeFileName'),
    uploadResumeBtn: g('uploadResumeBtn'),
    resumePreview:   g('resumePreview'),
    resumeStatus:    g('resumeStatus'),
    step2Indicator:  g('step2Indicator'),

    // Job Role
    jobRole: g('jobRole'),

    // Generate buttons
    genHrBtn:         g('genHrBtn'),
    genTechnicalBtn:  g('genTechnicalBtn'),
    genBehavioralBtn: g('genBehavioralBtn'),
    generateTipsBtn:  g('generateTipsBtn'),
    generateBtn:      g('generateBtn'),

    // Generated badges
    hrBadge:         g('hrBadge'),
    technicalBadge:  g('technicalBadge'),
    behavioralBadge: g('behavioralBadge'),
    tipsBadge:       g('tipsBadge'),

    // Loading
    loadingOverlay:  g('loadingOverlay'),
    loadingTitle:    g('loadingTitle'),
    loadingSubtitle: g('loadingSubtitle'),

    // Results
    resultsArea:             g('resultsArea'),
    resultJobRole:           g('resultJobRole'),
    hrQuestionsContainer:    g('hrQuestionsContainer'),
    techQuestionsContainer:  g('technicalQuestionsContainer'),
    behavQuestionsContainer: g('behavioralQuestionsContainer'),
    tipsContainer:           g('tipsContainer'),
    downloadBtn:             g('downloadBtn'),

    // Tab nav buttons (just for active class highlight)
    tabNavHR:       document.querySelector('[data-tab="tabHR"]'),
    tabNavTech:     document.querySelector('[data-tab="tabTech"]'),
    tabNavBehavior: document.querySelector('[data-tab="tabBehavioral"]'),
    tabNavTips:     document.querySelector('[data-tab="tabTips"]'),

    // Tab pane divs
    tabHR:       g('tabHR'),
    tabTech:     g('tabTech'),
    tabBehavioral: g('tabBehavioral'),
    tabTips:     g('tabTips'),

    // KB
    kbDropZone:    g('kbDropZone'),
    kbFile:        g('kbFile'),
    kbFileName:    g('kbFileName'),
    uploadKbBtn:   g('uploadKbBtn'),
    clearKbBtn:    g('clearKbBtn'),
    kbChunkCount:  g('kbChunkCount'),
    kbStatusBadge: g('kbStatusBadge'),

    // Toast
    globalToast:  g('globalToast'),
    toastMessage: g('toastMessage'),
  };
}

/* ══════════════════════════════════════════════
   TOAST
══════════════════════════════════════════════ */
function showToast(message, type = 'info') {
  const toast = els.globalToast;
  toast.className = `toast align-items-center border-0 toast-${type}`;
  els.toastMessage.textContent = message;
  bootstrap.Toast.getOrCreateInstance(toast, { delay: 4500 }).show();
}

/* ══════════════════════════════════════════════
   LOADING OVERLAY
══════════════════════════════════════════════ */
function showLoading(title, subtitle = '') {
  els.loadingTitle.textContent    = title || 'IBM Granite is thinking…';
  els.loadingSubtitle.textContent = subtitle;
  els.loadingOverlay.classList.add('active');
  document.body.style.overflow = 'hidden';
}
function hideLoading() {
  els.loadingOverlay.classList.remove('active');
  document.body.style.overflow = '';
}

/* ══════════════════════════════════════════════
   TAB SWITCHING  — pure DOM, no Bootstrap Tab JS
   This avoids all Bootstrap Tab state-management issues.
══════════════════════════════════════════════ */
function showTab(paneId) {
  // paneId: 'tabHR' | 'tabTech' | 'tabBehavioral' | 'tabTips'
  console.log('[tab] switching to', paneId);

  // Hide all panes
  ['tabHR', 'tabTech', 'tabBehavioral', 'tabTips'].forEach(id => {
    const pane = document.getElementById(id);
    if (pane) {
      pane.classList.remove('show', 'active');
    }
  });

  // Show target pane
  const target = document.getElementById(paneId);
  if (target) {
    target.classList.add('show', 'active');
  }

  // Update nav button active states
  document.querySelectorAll('.results-tabs .nav-link').forEach(btn => {
    btn.classList.remove('active');
    if (btn.getAttribute('data-tab') === paneId) {
      btn.classList.add('active');
    }
  });
}

/* ══════════════════════════════════════════════
   RESULTS AREA
══════════════════════════════════════════════ */
function ensureResultsVisible(jobRole) {
  els.resultsArea.classList.remove('d-none');
  if (els.resultJobRole) els.resultJobRole.textContent = jobRole || State.jobRole;
}

/* ══════════════════════════════════════════════
   DRAG-AND-DROP UPLOAD ZONES
══════════════════════════════════════════════ */
function setupDropZone(zone, input, fileNameEl, onFileReady) {
  ['dragenter', 'dragover'].forEach(e =>
    zone.addEventListener(e, ev => { ev.preventDefault(); zone.classList.add('dragover'); })
  );
  ['dragleave', 'drop'].forEach(e =>
    zone.addEventListener(e, () => zone.classList.remove('dragover'))
  );
  zone.addEventListener('drop', ev => {
    ev.preventDefault();
    const file = ev.dataTransfer?.files?.[0];
    if (file) {
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      handleFileSelect(file, zone, fileNameEl, onFileReady);
    }
  });
  input.addEventListener('change', () => {
    const file = input.files?.[0];
    if (file) handleFileSelect(file, zone, fileNameEl, onFileReady);
  });
}
function handleFileSelect(file, zone, fileNameEl, onFileReady) {
  zone.classList.add('has-file');
  fileNameEl.textContent = `📄 ${file.name}`;
  onFileReady(file);
}

/* ══════════════════════════════════════════════
   GENERATE BUTTONS — enable/disable
══════════════════════════════════════════════ */
const ALL_GEN_BTNS = () => [
  els.genHrBtn, els.genTechnicalBtn, els.genBehavioralBtn,
  els.generateTipsBtn, els.generateBtn,
];

function updateButtonsOnJobRole() {
  const hasRole = els.jobRole.value.trim().length > 0;
  ALL_GEN_BTNS().forEach(btn => { if (btn) btn.disabled = !hasRole; });
}

/* ══════════════════════════════════════════════
   MARK CATEGORY AS GENERATED
   Only called when questions.length > 0 or tips is a non-empty object
══════════════════════════════════════════════ */
function markGenerated(category) {
  const badge = document.getElementById(`${category}Badge`);
  const card  = document.getElementById(`genCard-${category}`);
  if (badge) badge.classList.remove('d-none');
  if (card)  card.style.borderColor = 'var(--ibm-green)';
  console.log('[markGenerated]', category);
}

function unmarkGenerated(category) {
  const badge = document.getElementById(`${category}Badge`);
  const card  = document.getElementById(`genCard-${category}`);
  if (badge) badge.classList.add('d-none');
  if (card)  card.style.borderColor = '';
}

/* ══════════════════════════════════════════════
   GENERATE ONE CATEGORY
   POST /generate_questions  { job_role, categories: [cat] }
══════════════════════════════════════════════ */
async function generateCategory(category) {
  const jobRole = els.jobRole.value.trim();
  if (!jobRole) { showToast('Please enter a job role first.', 'error'); return; }
  State.jobRole = jobRole;

  const label = { hr: 'HR', technical: 'Technical', behavioral: 'Behavioral' }[category] || category;
  console.log(`[generate] category=${category} job_role=${jobRole}`);

  showLoading(`Generating ${label} questions…`, 'IBM Granite is crafting personalised questions from your resume');

  try {
    const res  = await fetch('/generate_questions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_role: jobRole, categories: [category] }),
    });
    const data = await res.json();
    hideLoading();

    console.log(`[generate] ${category} response:`, data);

    if (!res.ok || data.error) { showToast(data.error || `Error ${res.status}`, 'error'); return; }

    const questions = data.results?.[category]?.questions || [];
    console.log(`[generate] ${category}: ${questions.length} questions`);

    // Store in State
    State.store[category] = questions;

    // Render
    ensureResultsVisible(jobRole);
    renderCategory(category, questions);

    // Only mark generated if we actually got questions
    if (questions.length > 0) {
      markGenerated(category);
    } else {
      unmarkGenerated(category);
      showToast(`${label}: no questions returned. Try again.`, 'error');
      return;
    }

    // Switch to that tab
    const tabMap = { hr: 'tabHR', technical: 'tabTech', behavioral: 'tabBehavioral' };
    showTab(tabMap[category] || 'tabHR');

    setTimeout(() => els.resultsArea.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
    showToast(`${label} questions ready!`, 'success');

  } catch (err) {
    hideLoading();
    showToast('Network error — please try again.', 'error');
    console.error('[generate] error', err);
  }
}

/* ══════════════════════════════════════════════
   GENERATE ALL (HR + Technical + Behavioral)
   Makes one backend call, splits results by category
══════════════════════════════════════════════ */
async function generateAll() {
  const jobRole = els.jobRole.value.trim();
  if (!jobRole) { showToast('Please enter a job role first.', 'error'); return; }
  State.jobRole = jobRole;

  console.log('[generate-all] job_role=' + jobRole);
  showLoading('Generating all questions…', 'IBM Granite is crafting HR, Technical & Behavioral questions');

  try {
    const res  = await fetch('/generate_questions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_role: jobRole, categories: ['hr', 'technical', 'behavioral'] }),
    });
    const data = await res.json();
    hideLoading();

    console.log('[generate-all] response:', data);

    if (!res.ok || data.error) { showToast(data.error || `Error ${res.status}`, 'error'); return; }

    const results = data.results || {};
    ensureResultsVisible(jobRole);

    let firstTabWithContent = null;

    // Process each category independently
    for (const cat of ['hr', 'technical', 'behavioral']) {
      const questions = results[cat]?.questions || [];
      console.log(`[generate-all] ${cat}: ${questions.length} questions`);

      // Store in State regardless (even empty — overwrites stale data)
      State.store[cat] = questions;

      // Render into its container
      renderCategory(cat, questions);

      if (questions.length > 0) {
        markGenerated(cat);
        if (!firstTabWithContent) firstTabWithContent = cat;
      } else {
        unmarkGenerated(cat);
      }
    }

    // Switch to first tab that has content
    const tabMap = { hr: 'tabHR', technical: 'tabTech', behavioral: 'tabBehavioral' };
    showTab(tabMap[firstTabWithContent || 'hr']);

    setTimeout(() => els.resultsArea.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);

    const count = ['hr','technical','behavioral'].filter(c => (State.store[c] || []).length > 0).length;
    if (count > 0) {
      showToast(`${count} of 3 categories generated. Use the tabs to switch between them.`, 'success');
    } else {
      showToast('No questions were returned. Please try again.', 'error');
    }

  } catch (err) {
    hideLoading();
    showToast('Network error — please try again.', 'error');
    console.error('[generate-all] error', err);
  }
}

/* ══════════════════════════════════════════════
   GENERATE TIPS
   POST /generate_tips  { job_role }
══════════════════════════════════════════════ */
async function generateTips() {
  const jobRole = els.jobRole.value.trim();
  if (!jobRole) { showToast('Please enter a job role first.', 'error'); return; }
  State.jobRole = jobRole;

  console.log('[tips] job_role=' + jobRole);
  showLoading('Generating preparation tips…', 'IBM Granite is building your personalised study guide');

  try {
    const res  = await fetch('/generate_tips', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_role: jobRole }),
    });
    const data = await res.json();
    hideLoading();

    console.log('[tips] response:', data);

    if (!res.ok || data.error) { showToast(data.error || `Error ${res.status}`, 'error'); return; }

    // Store and render
    State.store.tips = data.tips;
    ensureResultsVisible(jobRole);
    renderTips(data.tips);
    markGenerated('tips');
    showTab('tabTips');

    setTimeout(() => els.resultsArea.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
    showToast('Preparation guide ready!', 'success');

  } catch (err) {
    hideLoading();
    showToast('Network error — please try again.', 'error');
    console.error('[tips] error', err);
  }
}

/* ══════════════════════════════════════════════
   RENDER DISPATCHER  (called by generate + tab switch)
══════════════════════════════════════════════ */
function renderCategory(category, questions) {
  if (category === 'hr') renderHRQuestions(questions);
  else if (category === 'technical')  renderTechnicalQuestions(questions);
  else if (category === 'behavioral') renderBehavioralQuestions(questions);
}

/* ── HR Questions ────────────────────────────────────────────────── */
function renderHRQuestions(questions) {
  console.log('[render] HR:', questions.length);
  els.hrQuestionsContainer.innerHTML = questions.length
    ? questions.map((q, i) => buildCard(i, q, 'hr')).join('')
    : emptyState('No HR questions yet — click <strong>Generate</strong> on the HR card above.');
}

/* ── Technical Questions ─────────────────────────────────────────── */
function renderTechnicalQuestions(questions) {
  console.log('[render] Technical:', questions.length);
  els.techQuestionsContainer.innerHTML = questions.length
    ? questions.map((q, i) => buildCard(i, q, 'technical')).join('')
    : emptyState('No Technical questions yet — click <strong>Generate</strong> on the Technical card above.');
}

/* ── Behavioral Questions ─────────────────────────────────────────── */
function renderBehavioralQuestions(questions) {
  console.log('[render] Behavioral:', questions.length);
  els.behavQuestionsContainer.innerHTML = questions.length
    ? questions.map((q, i) => buildCard(i, q, 'behavioral')).join('')
    : emptyState('No Behavioral questions yet — click <strong>Generate</strong> on the Behavioral card above.');
}

/* ── Question Card Builder ───────────────────────────────────────── */
function buildCard(idx, q, type) {
  let body = '';

  if (type === 'hr') {
    if (q.why_asked)    body += qSection('bi-question-circle', 'Why Asked',    esc(q.why_asked));
    if (q.model_answer) body += qSection('bi-patch-check',    'Model Answer', esc(q.model_answer));

  } else if (type === 'technical') {
    const raw     = (q.difficulty || 'Foundational').toLowerCase();
    const cls     = raw.includes('advanc') ? 'diff-advanced' : raw.includes('inter') ? 'diff-intermediate' : 'diff-foundational';
    const badge   = `<span class="difficulty-badge ${cls} ms-2">${esc(q.difficulty || 'Foundational')}</span>`;
    if (q.concepts)     body += qSection('bi-lightbulb',   'Key Concepts', esc(q.concepts));
    if (q.model_answer) body += qSection('bi-patch-check', 'Model Answer', esc(q.model_answer));
    return cardShell(idx, `${esc(q.question || '')}${badge}`, body);

  } else if (type === 'behavioral') {
    if (q.competency) body += qSection('bi-award', 'Competency', esc(q.competency));
    const star = q.model_answer;
    if (star) {
      const starHtml = (typeof star === 'object' && !Array.isArray(star))
        ? `<div class="star-grid">${['situation','task','action','result']
            .filter(k => star[k])
            .map(k => `<div class="star-item"><div class="star-label">${k[0].toUpperCase()+k.slice(1)}</div><div class="star-text">${esc(star[k])}</div></div>`)
            .join('')}</div>`
        : `<div class="q-section-content">${esc(String(star))}</div>`;
      body += `<div class="q-section"><div class="q-section-title"><i class="bi bi-stars"></i>STAR Answer</div>${starHtml}</div>`;
    }
  }

  return cardShell(idx, esc(q.question || ''), body);
}

function cardShell(idx, questionHtml, bodyHtml) {
  return `
    <div class="question-card fade-in" style="animation-delay:${idx * .05}s">
      <div class="question-header" onclick="toggleCard(this.parentElement)">
        <div class="q-number">${idx + 1}</div>
        <div class="q-text">${questionHtml}</div>
        <i class="bi bi-chevron-down q-chevron"></i>
      </div>
      <div class="question-body">${bodyHtml}</div>
    </div>`;
}

function qSection(icon, title, contentHtml) {
  return `<div class="q-section">
    <div class="q-section-title"><i class="bi ${icon}"></i>${title}</div>
    <div class="q-section-content">${contentHtml}</div>
  </div>`;
}

/* ══════════════════════════════════════════════
   RENDER PREPARATION TIPS
══════════════════════════════════════════════ */
function renderTips(tips) {
  console.log('[render] Tips:', tips);
  if (!tips || typeof tips !== 'object') {
    els.tipsContainer.innerHTML = emptyState('No preparation tips yet — click <strong>Generate</strong> on the Preparation Tips card above.');
    return;
  }
  if (tips.prose_tips) {
    els.tipsContainer.innerHTML = `
      <div class="tips-card fade-in">
        <div class="tips-card-title"><i class="bi bi-lightbulb"></i>Interview Preparation Tips</div>
        <div style="font-size:.875rem;color:var(--text-secondary);line-height:1.8;white-space:pre-wrap">${esc(tips.prose_tips)}</div>
      </div>`;
    return;
  }

  const sections = [
    { key: 'strengths',        icon: 'bi-trophy',               title: 'Your Strengths',                   type: 'chips', cls: 'strength-chip' },
    { key: 'gaps_to_address',  icon: 'bi-exclamation-triangle', title: 'Areas to Address',                 type: 'chips', cls: 'gap-chip' },
    { key: 'technical_tips',   icon: 'bi-code-slash',           title: 'Technical Preparation',            type: 'list' },
    { key: 'hr_tips',          icon: 'bi-people',               title: 'HR Round Tips',                    type: 'list' },
    { key: 'behavioral_tips',  icon: 'bi-stars',                title: 'Behavioral Round (STAR Method)',   type: 'list' },
    { key: 'topics_to_revise', icon: 'bi-journal-check',        title: 'Topics to Revise',                 type: 'list' },
    { key: 'common_mistakes',  icon: 'bi-x-circle',             title: 'Common Mistakes to Avoid',         type: 'list' },
    { key: 'company_strategy', icon: 'bi-building',             title: 'Company Research Strategy',        type: 'list' },
    { key: 'questions_to_ask', icon: 'bi-chat-dots',            title: 'Questions to Ask the Interviewer', type: 'list' },
    { key: 'salary_tip',       icon: 'bi-cash-coin',            title: 'Salary Negotiation',               type: 'text' },
    // legacy key aliases
    { key: 'day_before_tips',              icon: 'bi-moon-stars', title: 'Day Before Interview',  type: 'list' },
    { key: 'day_of_tips',                  icon: 'bi-sunrise',    title: 'Day of Interview',      type: 'list' },
    { key: 'questions_to_ask_interviewer', icon: 'bi-chat-dots',  title: 'Questions to Ask',      type: 'list' },
    { key: 'salary_negotiation_tip',       icon: 'bi-cash-coin',  title: 'Salary Negotiation',    type: 'text' },
    { key: 'preparation_plan',             icon: 'bi-journal-check', title: 'Preparation Plan',   type: 'plan' },
  ];

  const rendered = new Set();
  let html = '<div class="tips-grid fade-in">';

  for (const sec of sections) {
    const val = tips[sec.key];
    if (!val || rendered.has(sec.key)) continue;
    rendered.add(sec.key);
    html += `<div class="tips-card"><div class="tips-card-title"><i class="bi ${sec.icon}"></i>${sec.title}</div>`;
    if (sec.type === 'chips' && Array.isArray(val))
      html += `<div>${val.map(v => `<span class="${sec.cls}">${esc(v)}</span>`).join('')}</div>`;
    else if (sec.type === 'list' && Array.isArray(val))
      html += `<ul class="tips-list">${val.map(v => `<li>${esc(String(v))}</li>`).join('')}</ul>`;
    else if (sec.type === 'text')
      html += `<p style="font-size:.875rem;color:var(--text-secondary);margin:0;line-height:1.7">${esc(String(val))}</p>`;
    else if (sec.type === 'plan' && Array.isArray(val))
      html += val.map(a => `<div class="mb-2"><strong style="font-size:.85rem;color:var(--text-primary)">${esc(a.area||'')}</strong>
        <ul class="tips-list mt-1">${(a.tips||[]).map(t=>`<li>${esc(t)}</li>`).join('')}</ul></div>`).join('');
    html += '</div>';
  }

  // Render unknown keys the model may have returned
  for (const [key, val] of Object.entries(tips)) {
    if (rendered.has(key) || key === 'prose_tips') continue;
    html += `<div class="tips-card"><div class="tips-card-title"><i class="bi bi-info-circle"></i>${esc(key.replace(/_/g,' '))}</div>`;
    html += Array.isArray(val)
      ? `<ul class="tips-list">${val.map(v => `<li>${esc(String(v))}</li>`).join('')}</ul>`
      : `<p style="font-size:.875rem;color:var(--text-secondary);margin:0">${esc(String(val))}</p>`;
    html += '</div>';
  }
  html += '</div>';
  els.tipsContainer.innerHTML = html;
}

/* ══════════════════════════════════════════════
   RESUME UPLOAD
══════════════════════════════════════════════ */
function initResumeUpload() {
  setupDropZone(
    els.resumeDropZone, els.resumeFile, els.resumeFileName,
    () => { els.uploadResumeBtn.disabled = false; }
  );

  els.uploadResumeBtn.addEventListener('click', async () => {
    const file = els.resumeFile.files?.[0];
    if (!file) return;

    console.log('[resume] uploading', file.name);
    showLoading('Parsing your resume…', 'IBM Granite is extracting all skills, experience, projects and more');

    const fd = new FormData();
    fd.append('resume', file);

    try {
      const res  = await fetch('/upload_resume', { method: 'POST', body: fd });
      const data = await res.json();
      hideLoading();

      console.log('[resume] response:', data);

      if (data.error) { showToast(data.error, 'error'); return; }

      renderResumePreview(data.data);
      unlockStep2();
      showToast('Resume parsed — enter a job role and generate questions!', 'success');

    } catch (err) {
      hideLoading();
      showToast('Network error — please try again.', 'error');
      console.error('[resume] error', err);
    }
  });
}

/* ── Full Resume Preview ─────────────────────────────────────────── */
function renderResumePreview(d) {
  if (!d || d.parse_error) {
    els.resumePreview.innerHTML = `
      <div class="resume-info fade-in">
        <div class="resume-name"><i class="bi bi-person-circle me-2"></i>Resume Uploaded</div>
        <p style="font-size:.85rem;color:var(--text-secondary);margin-top:.5rem">
          Content captured — questions will be generated using the full resume text.
        </p>
      </div>`;
  } else {
    let h = '<div class="resume-info fade-in">';

    /* ── Header ── */
    h += `<div>
      <div class="resume-name"><i class="bi bi-person-circle me-2"></i>${esc(d.name || 'Candidate')}</div>
      <div style="display:flex;flex-wrap:wrap;gap:.4rem;margin-top:.35rem;font-size:.78rem;color:var(--text-muted)">`;
    if (d.email)    h += `<span><i class="bi bi-envelope me-1"></i>${esc(d.email)}</span>`;
    if (d.phone)    h += `<span><i class="bi bi-telephone me-1"></i>${esc(d.phone)}</span>`;
    if (d.location) h += `<span><i class="bi bi-geo-alt me-1"></i>${esc(d.location)}</span>`;
    if (d.linkedin) h += `<span><i class="bi bi-linkedin me-1"></i>${esc(d.linkedin)}</span>`;
    if (d.github)   h += `<span><i class="bi bi-github me-1"></i>${esc(d.github)}</span>`;
    h += '</div></div>';

    /* ── Summary ── */
    if (d.summary) {
      h += rSection('bi-person-lines-fill', 'Summary',
        `<p style="font-size:.82rem;color:var(--text-secondary);margin:0;line-height:1.6">${esc(d.summary)}</p>`);
    }

    /* ── Skills ── */
    if (d.skills?.length) {
      h += rSection('bi-tools', 'Skills',
        d.skills.map(s => `<span class="skill-chip">${esc(s)}</span>`).join(''));
    }

    /* ── Education ── */
    if (d.education?.length) {
      h += rSection('bi-mortarboard', 'Education',
        d.education.map(e => `
          <div class="resume-item mb-2">
            <strong>${esc(e.degree || '')}</strong> — ${esc(e.institution || '')}
            <span style="color:var(--text-muted);font-size:.78rem;margin-left:.4rem">${esc(e.year || '')}</span>
            ${e.gpa ? `<span class="skill-chip ms-1" style="font-size:.72rem">GPA ${esc(e.gpa)}</span>` : ''}
          </div>`).join(''));
    }

    /* ── Experience ── */
    if (d.experience?.length) {
      h += rSection('bi-briefcase', 'Experience',
        d.experience.map(e => `
          <div class="resume-item mb-3">
            <div><strong>${esc(e.title || '')}</strong>
              <span style="color:var(--ibm-blue-light);font-size:.8rem;margin-left:.4rem">@ ${esc(e.company || '')}</span>
              <span style="color:var(--text-muted);font-size:.75rem;margin-left:.4rem">${esc(e.duration || '')}</span>
            </div>
            ${(e.responsibilities || []).length ? `
              <ul style="margin:.35rem 0 0 1rem;padding:0;font-size:.8rem;color:var(--text-secondary)">
                ${e.responsibilities.map(r => `<li>${esc(r)}</li>`).join('')}
              </ul>` : ''}
          </div>`).join(''));
    }

    /* ── Internships ── */
    if (d.internships?.length) {
      h += rSection('bi-briefcase-fill', 'Internships',
        d.internships.map(e => `
          <div class="resume-item mb-2">
            <div><strong>${esc(e.title || '')}</strong>
              <span style="color:var(--ibm-blue-light);font-size:.8rem;margin-left:.4rem">@ ${esc(e.company || '')}</span>
              <span style="color:var(--text-muted);font-size:.75rem;margin-left:.4rem">${esc(e.duration || '')}</span>
            </div>
          </div>`).join(''));
    }

    /* ── Projects ── */
    if (d.projects?.length) {
      h += rSection('bi-code-square', 'Projects',
        d.projects.map(p => `
          <div class="resume-item mb-3">
            <div><strong>${esc(p.name || '')}</strong>
              ${p.link ? `<a href="${esc(p.link)}" style="font-size:.75rem;color:var(--ibm-blue-light);margin-left:.4rem" target="_blank"><i class="bi bi-box-arrow-up-right me-1"></i>Link</a>` : ''}
            </div>
            <div style="font-size:.8rem;color:var(--text-secondary);margin:.2rem 0">${esc(p.description || '')}</div>
            <div>${(p.technologies || []).map(t => `<span class="skill-chip">${esc(t)}</span>`).join('')}</div>
          </div>`).join(''));
    }

    /* ── Certifications ── */
    if (d.certifications?.length) {
      h += rSection('bi-patch-check-fill', 'Certifications',
        d.certifications.map(c => `<div class="resume-item" style="font-size:.82rem"><i class="bi bi-check2-circle text-success me-1"></i>${esc(c)}</div>`).join(''));
    }

    /* ── Achievements ── */
    if (d.achievements?.length) {
      h += rSection('bi-trophy-fill', 'Achievements',
        d.achievements.map(a => `<div class="resume-item" style="font-size:.82rem"><i class="bi bi-star-fill text-warning me-1"></i>${esc(a)}</div>`).join(''));
    }

    /* ── Languages ── */
    if (d.languages?.length) {
      h += rSection('bi-translate', 'Languages',
        d.languages.map(l => `<span class="skill-chip">${esc(l)}</span>`).join(''));
    }

    h += '</div>';
    els.resumePreview.innerHTML = h;
  }

  // Mark Step 1 done
  document.querySelector('#step1 .step-dot')?.replaceChildren(
    Object.assign(document.createElement('i'), { className: 'bi bi-check' })
  );
  document.querySelector('#step1 .step-indicator')?.classList.add('done');
  if (els.resumeStatus) els.resumeStatus.innerHTML = '<span class="badge bg-success">✓ Parsed</span>';
}

function rSection(icon, title, contentHtml) {
  return `<div style="margin-top:.85rem">
    <div class="resume-section-title"><i class="bi ${icon} me-1"></i>${title}</div>
    <div>${contentHtml}</div>
  </div>`;
}

/* ══════════════════════════════════════════════
   UNLOCK STEP 2
══════════════════════════════════════════════ */
function unlockStep2() {
  els.jobRole.disabled = false;
  els.jobRole.focus();
  els.step2Indicator?.classList.add('active');
  els.jobRole.addEventListener('input', updateButtonsOnJobRole);
  updateButtonsOnJobRole();
}

/* ══════════════════════════════════════════════
   ACCORDION TOGGLE  (global, called by inline onclick)
══════════════════════════════════════════════ */
window.toggleCard = (card) => card.classList.toggle('open');

/* ══════════════════════════════════════════════
   KNOWLEDGE BASE
══════════════════════════════════════════════ */
function initKB() {
  setupDropZone(els.kbDropZone, els.kbFile, els.kbFileName,
    () => { els.uploadKbBtn.disabled = false; });

  els.uploadKbBtn.addEventListener('click', async () => {
    const file = els.kbFile.files?.[0];
    if (!file) return;
    showLoading('Ingesting document…', 'Chunking and embedding into the knowledge base');
    const fd = new FormData();
    fd.append('kb_file', file);
    try {
      const res  = await fetch('/upload_kb', { method: 'POST', body: fd });
      const data = await res.json();
      hideLoading();
      if (data.error) { showToast(data.error, 'error'); return; }
      showToast(`Added ${data.chunks_added} chunks from "${data.filename}"`, 'success');
      updateKbCount(data.total_chunks);
      els.kbDropZone.classList.remove('has-file');
      els.kbFileName.textContent = '';
      els.uploadKbBtn.disabled = true;
      els.kbFile.value = '';
    } catch (err) {
      hideLoading();
      showToast('KB upload error.', 'error');
      console.error(err);
    }
  });

  els.clearKbBtn.addEventListener('click', async () => {
    if (!confirm('Clear the entire knowledge base?')) return;
    try { await fetch('/clear_kb', { method: 'POST' }); updateKbCount(0); showToast('KB cleared.', 'info'); }
    catch { showToast('Failed.', 'error'); }
  });
}

function updateKbCount(n) {
  if (els.kbChunkCount)  els.kbChunkCount.textContent = n;
  if (els.kbStatusBadge) {
    const icon = n > 0 ? 'bi-circle-fill text-success' : 'bi-circle-fill text-warning';
    els.kbStatusBadge.innerHTML = `<i class="bi ${icon} me-1"></i>KB: ${n} chunk${n !== 1 ? 's' : ''}`;
  }
}

async function fetchKbStatus() {
  try { const d = await (await fetch('/kb_status')).json(); updateKbCount(d.total_chunks || 0); } catch (_) {}
}

/* ══════════════════════════════════════════════
   DOWNLOAD
══════════════════════════════════════════════ */
function initDownload() {
  if (els.downloadBtn) els.downloadBtn.addEventListener('click', () => window.print());
}

/* ══════════════════════════════════════════════
   HELPERS
══════════════════════════════════════════════ */
function esc(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/\n/g, '<br>');
}
function emptyState(msg) {
  return `<div class="empty-state py-5">
    <i class="bi bi-inbox" style="font-size:2.5rem"></i>
    <p style="max-width:300px">${msg}</p>
  </div>`;
}

/* ══════════════════════════════════════════════
   INIT
══════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  resolveEls();
  initResumeUpload();
  initKB();
  initDownload();
  fetchKbStatus();

  // Per-category generate buttons
  els.genHrBtn.addEventListener('click',         () => generateCategory('hr'));
  els.genTechnicalBtn.addEventListener('click',  () => generateCategory('technical'));
  els.genBehavioralBtn.addEventListener('click', () => generateCategory('behavioral'));
  els.generateTipsBtn.addEventListener('click',  () => generateTips());
  els.generateBtn.addEventListener('click',      () => generateAll());

  // Tab nav buttons — wire up pure-DOM tab switching
  document.querySelectorAll('.results-tabs .nav-link[data-tab]').forEach(btn => {
    btn.addEventListener('click', () => {
      const paneId = btn.getAttribute('data-tab');
      showTab(paneId);
    });
  });

  // Smooth scroll for navbar anchors
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const t = document.querySelector(a.getAttribute('href'));
      if (t) { e.preventDefault(); t.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
    });
  });

  console.log('[init] Interview Trainer Agent ready.');
});
