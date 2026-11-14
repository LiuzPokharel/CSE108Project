const message = document.getElementById("message");
const coursesView = document.getElementById("courses-view");
const rosterView = document.getElementById("roster-view");

function showMessage(text = "", kind = "error") {
  message.textContent = text;
  message.classList.toggle("is-error", kind === "error" && Boolean(text));
}

function courseRow(course) {
  const tr = document.createElement("tr");
  const nameCell = document.createElement("td");
  const link = document.createElement("a");
  link.href = `#course-${course.id}`;
  link.className = "course-link";
  link.textContent = course.name;
  link.addEventListener("click", (event) => {
    event.preventDefault();
    loadRoster(course.id);
  });
  nameCell.append(link);
  tr.append(nameCell);

  for (const value of [course.teacher, course.time, `${course.enrolled_count}/${course.capacity}`]) {
    const td = document.createElement("td");
    td.textContent = value;
    tr.append(td);
  }
  return tr;
}

async function loadCourses() {
  const response = await fetch("/api/teacher/courses");
  if (response.status === 401) {
    window.location.href = "/";
    return;
  }
  if (!response.ok) {
    showMessage("Couldn't load your courses. Please refresh the page.");
    return;
  }

  const courses = await response.json();
  document.getElementById("course-rows").replaceChildren(...courses.map(courseRow));
  document.getElementById("courses-empty").hidden = courses.length > 0;
}

function studentRow(student, courseId) {
  const tr = document.createElement("tr");
  const name = document.createElement("td");
  name.textContent = student.name;
  tr.append(name);

  const gradeCell = document.createElement("td");
  const input = document.createElement("input");
  input.className = "grade-input";
  input.type = "number";
  input.min = "0";
  input.max = "100";
  input.step = "any";
  input.value = student.grade ?? "";
  input.placeholder = "—";
  input.setAttribute("aria-label", `Grade for ${student.name}`);
  input.addEventListener("focus", () => { input.dataset.previousValue = input.value; });
  input.addEventListener("change", () => saveGrade(courseId, student, input));
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") input.blur();
    if (event.key === "Escape") {
      input.value = input.dataset.previousValue ?? "";
      input.blur();
    }
  });
  gradeCell.append(input);
  tr.append(gradeCell);
  return tr;
}

async function loadRoster(courseId) {
  showMessage();
  try {
    const response = await fetch(`/api/teacher/courses/${courseId}/students`);
    if (response.status === 401) {
      window.location.href = "/";
      return;
    }
    const data = await response.json();
    if (!response.ok) {
      showMessage(data.error || "Couldn't load this roster.");
      return;
    }

    document.getElementById("roster-title").textContent = data.course.name;
    document.getElementById("student-rows").replaceChildren(
      ...data.students.map((student) => studentRow(student, courseId))
    );
    document.getElementById("students-empty").hidden = data.students.length > 0;
    coursesView.hidden = true;
    rosterView.hidden = false;
  } catch {
    showMessage("Couldn't reach the server. Please try again.");
  }
}

async function saveGrade(courseId, student, input) {
  if (input.value !== "" && !input.checkValidity()) {
    input.reportValidity();
    return;
  }
  const previousValue = input.dataset.previousValue ?? "";
  if (input.value === previousValue) return;

  try {
    const response = await fetch(`/api/teacher/courses/${courseId}/students/${student.id}/grade`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ grade: input.value === "" ? null : Number(input.value) }),
    });
    const data = await response.json();
    if (!response.ok) {
      input.value = previousValue;
      showMessage(data.error || "Couldn't save this grade.");
      return;
    }
    input.dataset.previousValue = input.value;
    showMessage("Grade saved.", "success");
  } catch {
    input.value = previousValue;
    showMessage("Couldn't reach the server. Please try again.");
  }
}

document.getElementById("back-to-courses").addEventListener("click", () => {
  rosterView.hidden = true;
  coursesView.hidden = false;
  showMessage();
  loadCourses();
});

loadCourses().catch(() => showMessage("Couldn't reach the server. Please refresh the page."));
