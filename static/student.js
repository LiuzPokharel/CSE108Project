const message = document.getElementById("message");

// --- Tabs: show the panel whose tab was clicked, hide the other ---
const tabs = document.querySelectorAll('[role="tab"]');
tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((t) => {
      const active = t === tab;
      t.setAttribute("aria-selected", active);
      document.getElementById(t.getAttribute("aria-controls")).hidden = !active;
    });
  });
});

// --- Tables ---
function row(course) {
  // textContent, not innerHTML: an admin can type anything into a course name, so never treat it as HTML
  const tr = document.createElement("tr");
  for (const text of [course.name, course.teacher, course.time, `${course.enrolled_count}/${course.capacity}`]) {
    const td = document.createElement("td");
    td.textContent = text;
    tr.append(td);
  }
  return tr;
}

function actionCell(course) {
  // Mockup: "−" to drop a course you're in, "+" to add one with room, nothing if it's full
  const td = document.createElement("td");
  td.className = "action";
  if (!course.enrolled && course.enrolled_count >= course.capacity) return td;

  const button = document.createElement("button");
  button.className = course.enrolled ? "drop" : "add";
  button.textContent = course.enrolled ? "−" : "+";
  button.setAttribute("aria-label", `${course.enrolled ? "Drop" : "Add"} ${course.name}`);
  button.addEventListener("click", () => change(course.enrolled ? "DELETE" : "POST", course));
  td.append(button);
  return td;
}

function render(courses) {
  const mine = courses.filter((c) => c.enrolled);
  document.getElementById("mine-rows").replaceChildren(...mine.map(row));
  document.getElementById("mine-empty").hidden = mine.length > 0;
  document.getElementById("add-rows").replaceChildren(
    ...courses.map((c) => {
      const tr = row(c);
      tr.append(actionCell(c));
      return tr;
    })
  );
}

// --- Talking to the server ---
async function load() {
  const response = await fetch("/api/courses");
  if (!response.ok) {
    window.location.href = "/";   // signed out
    return;
  }
  render(await response.json());
}

async function change(method, course) {
  message.textContent = "";
  const response = await fetch(`/api/courses/${course.id}/enroll`, { method });
  if (!response.ok) {
    // e.g. someone else took the last seat since this page loaded
    message.textContent = (await response.json()).error;
  }
  load();   // reload either way so counts are fresh
}

load();
