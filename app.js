// Student Management System - frontend logic (Fetch API, no page reloads)
const API = "http://127.0.0.1:5000/api/students";
const PASS_MARK = 40;

const $ = (id) => document.getElementById(id);
const form = $("student-form");
const fields = ["roll_no", "name", "class", "marks", "contact", "email"];
let students = [];
let searchTimer;

// ---------- API helper ----------
async function api(url, options = {}) {
  let res;
  try {
    res = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw { message: "Cannot reach the server. Is the Flask backend running on port 5000?" };
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw { message: body.error || "Request failed.", details: body.details || {} };
  return body;
}

// ---------- UI helpers ----------
function toast(msg, isError = false) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.toggle("error", isError);
  t.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => t.classList.remove("show"), 3000);
}

function showErrors(errors = {}) {
  fields.forEach((f) => {
    const msg = errors[f] || "";
    document.querySelector(`.err[data-for="${f}"]`).textContent = msg;
    $(f).classList.toggle("invalid", Boolean(msg));
  });
}

// Client-side validation (mirrors server rules)
function validate(d) {
  const e = {};
  if (!d.roll_no) e.roll_no = "Roll number is required.";
  else if (!/^[A-Za-z0-9\-/]{1,20}$/.test(d.roll_no)) e.roll_no = "Use letters, digits, '-' or '/'.";
  if (!d.name) e.name = "Name is required.";
  else if (!/^[A-Za-z][A-Za-z .'\-]{0,59}$/.test(d.name)) e.name = "Name must contain letters only.";
  if (!d.class) e.class = "Class is required.";
  const m = Number(d.marks);
  if (d.marks === "" || Number.isNaN(m) || m < 0 || m > 100) e.marks = "Enter marks between 0 and 100.";
  if (!/^[6-9]\d{9}$/.test(d.contact)) e.contact = "Enter a valid 10-digit mobile number.";
  if (d.email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(d.email)) e.email = "Email format is invalid.";
  return e;
}

function readForm() {
  const d = {};
  fields.forEach((f) => (d[f] = $(f).value.trim()));
  return d;
}

function resetForm() {
  form.reset();
  $("student-id").value = "";
  $("form-title").textContent = "Add student";
  $("save-btn").textContent = "Add student";
  $("cancel-btn").hidden = true;
  showErrors();
  render();
}

// ---------- rendering ----------
function cell(text, cls) {
  const td = document.createElement("td");
  td.textContent = text; // textContent prevents HTML injection
  if (cls) td.className = cls;
  return td;
}

function render() {
  const tbody = $("rows");
  tbody.replaceChildren();
  const editingId = $("student-id").value;

  students.forEach((s) => {
    const tr = document.createElement("tr");
    if (String(s.id) === editingId) tr.classList.add("editing");
    tr.append(
      cell(s.roll_no),
      cell(s.name),
      cell(s.class),
      cell(s.marks, "num " + (s.marks >= PASS_MARK ? "marks-pass" : "marks-fail")),
      cell(s.contact)
    );
    const td = document.createElement("td");
    td.className = "btns";
    const edit = document.createElement("button");
    edit.className = "small";
    edit.textContent = "Edit";
    edit.setAttribute("aria-label", `Edit ${s.name}`);
    edit.onclick = () => startEdit(s);
    const del = document.createElement("button");
    del.className = "small danger";
    del.textContent = "Delete";
    del.setAttribute("aria-label", `Delete ${s.name}`);
    del.onclick = () => removeStudent(s);
    td.append(edit, del);
    tr.append(td);
    tbody.append(tr);
  });

  const q = $("search").value.trim();
  const empty = $("empty");
  empty.hidden = students.length > 0;
  empty.textContent = q ? `No student matches “${q}”. Check the spelling or roll number.` : "No students yet. Add the first one using the form.";

  const avg = students.length ? students.reduce((a, s) => a + s.marks, 0) / students.length : 0;
  $("summary").textContent = students.length
    ? `${students.length} shown · average marks ${avg.toFixed(1)}`
    : "";
}

// ---------- actions ----------
async function loadStudents() {
  const q = $("search").value.trim();
  try {
    students = await api(q ? `${API}?q=${encodeURIComponent(q)}` : API);
    render();
  } catch (err) {
    toast(err.message, true);
  }
}

function startEdit(s) {
  $("student-id").value = s.id;
  fields.forEach((f) => ($(f).value = s[f] ?? ""));
  $("form-title").textContent = `Edit ${s.name}`;
  $("save-btn").textContent = "Save changes";
  $("cancel-btn").hidden = false;
  showErrors();
  render();
  $("name").focus();
}

async function removeStudent(s) {
  if (!confirm(`Delete ${s.name} (${s.roll_no})? This cannot be undone.`)) return;
  try {
    await api(`${API}/${s.id}`, { method: "DELETE" });
    if ($("student-id").value === String(s.id)) resetForm();
    toast("Student deleted.");
    await loadStudents();
  } catch (err) {
    toast(err.message, true);
    await loadStudents(); // e.g. already deleted elsewhere
  }
}

form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const data = readForm();
  const errors = validate(data);
  showErrors(errors);
  if (Object.keys(errors).length) return;

  const id = $("student-id").value;
  const btn = $("save-btn");
  btn.disabled = true;
  try {
    await api(id ? `${API}/${id}` : API, {
      method: id ? "PUT" : "POST",
      body: JSON.stringify({ ...data, marks: Number(data.marks) }),
    });
    toast(id ? "Changes saved." : "Student added.");
    resetForm();
    await loadStudents();
  } catch (err) {
    showErrors(err.details); // server-side errors e.g. duplicate roll number
    toast(err.message, true);
  } finally {
    btn.disabled = false;
  }
});

$("cancel-btn").addEventListener("click", resetForm);
$("search").addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadStudents, 200); // debounce
});

loadStudents();
