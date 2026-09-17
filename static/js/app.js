const form = document.querySelector("#todo-form");
const input = document.querySelector("#todo-input");
const list = document.querySelector("#todo-list");
const empty = document.querySelector("#empty");
const count = document.querySelector("#count");
const statusEl = document.querySelector("#status");
const filters = document.querySelectorAll(".filter");

let todos = [];
let currentFilter = "all";

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const title = input.value.trim();
  if (!title) return;

  try {
    const created = await request("/api/todos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    });
    todos.unshift(created);
    input.value = "";
    render();
  } catch (error) {
    showStatus(error.message);
  }
});

filters.forEach((button) => {
  button.addEventListener("click", () => {
    currentFilter = button.dataset.filter;
    filters.forEach((item) => item.classList.toggle("is-active", item === button));
    render();
  });
});

async function loadTodos() {
  try {
    todos = await request("/api/todos");
    render();
  } catch (error) {
    showStatus(error.message);
  }
}

async function request(url, options) {
  const response = await fetch(url, options);
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || "요청을 처리하지 못했습니다.");
  }
  return data;
}

function visibleTodos() {
  if (currentFilter === "active") return todos.filter((todo) => !todo.completed);
  if (currentFilter === "completed") return todos.filter((todo) => todo.completed);
  return todos;
}

function render() {
  const items = visibleTodos();
  list.replaceChildren();
  empty.hidden = items.length !== 0;
  count.textContent = `${todos.length}개의 할 일`;

  items.forEach((todo) => {
    const li = document.createElement("li");
    li.className = `todo-item${todo.completed ? " is-done" : ""}`;
    li.dataset.id = String(todo.id);

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.className = "check";
    checkbox.checked = todo.completed;
    checkbox.setAttribute("aria-label", "완료 표시");
    checkbox.addEventListener("change", () => toggleTodo(todo.id, checkbox.checked));

    const body = document.createElement("div");
    const title = document.createElement("p");
    title.className = "title";
    title.textContent = todo.title;

    const meta = document.createElement("p");
    meta.className = "meta";
    meta.textContent = todo.created_at;

    body.append(title, meta);

    const actions = document.createElement("div");
    actions.className = "actions";

    const editButton = document.createElement("button");
    editButton.type = "button";
    editButton.className = "icon-btn";
    editButton.textContent = "수정";
    editButton.addEventListener("click", () => startEdit(li, todo));

    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "icon-btn delete";
    deleteButton.textContent = "삭제";
    deleteButton.addEventListener("click", () => deleteTodo(todo.id));

    actions.append(editButton, deleteButton);
    li.append(checkbox, body, actions);
    list.append(li);
  });
}

function startEdit(li, todo) {
  const inputEl = document.createElement("input");
  inputEl.type = "text";
  inputEl.value = todo.title;
  inputEl.maxLength = 200;

  const saveButton = document.createElement("button");
  saveButton.type = "button";
  saveButton.className = "icon-btn";
  saveButton.textContent = "저장";

  const cancelButton = document.createElement("button");
  cancelButton.type = "button";
  cancelButton.className = "icon-btn";
  cancelButton.textContent = "취소";

  li.children[1].replaceChildren(inputEl);
  li.children[2].replaceChildren(saveButton, cancelButton);
  inputEl.focus();
  inputEl.select();

  const finish = async (shouldSave) => {
    if (!shouldSave) {
      render();
      return;
    }
    const title = inputEl.value.trim();
    if (!title || title === todo.title) {
      render();
      return;
    }
    await updateTodo(todo.id, { title });
  };

  saveButton.addEventListener("click", () => finish(true));
  cancelButton.addEventListener("click", () => finish(false));
  inputEl.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      finish(true);
    }
    if (event.key === "Escape") {
      event.preventDefault();
      finish(false);
    }
  });
}

async function toggleTodo(id, completed) {
  await updateTodo(id, { completed });
}

async function updateTodo(id, payload) {
  try {
    const updated = await request(`/api/todos/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    todos = todos.map((todo) => (todo.id === id ? updated : todo));
    render();
  } catch (error) {
    showStatus(error.message);
    render();
  }
}

async function deleteTodo(id) {
  try {
    await request(`/api/todos/${id}`, { method: "DELETE" });
    todos = todos.filter((todo) => todo.id !== id);
    render();
  } catch (error) {
    showStatus(error.message);
  }
}

function showStatus(message) {
  statusEl.hidden = false;
  statusEl.textContent = message;
}

loadTodos();
