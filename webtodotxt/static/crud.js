const API_BASE = "/task"; // change to your actual endpoint

function showErrorDialog(message) {
    alert(message);
    location.reload();
}

async function getLine(csfr, lineNumber) {
    const response = await fetch(`${API_BASE}/${lineNumber}`, {
        method: "GET",
        headers: {
            "Accept": "application/json",
            'X-CSRF-TOKEN': csfr
        }
    });
    if (!response.ok) {
        showErrorDialog(`GET failed: ${response.status}`);
        throw new Error(`GET failed: ${response.status}`);
    }
    return response.json();
}

async function putLine(csfr, lineNumber, data) {
    const response = await fetch(`${API_BASE}/${lineNumber}`, {
        method: "PUT",
        headers: {
            "Content-type": "application/json",
            'X-CSRF-TOKEN': csfr
        },
        body: JSON.stringify(data)
    });

    if (!response.ok) {
        showErrorDialog(`PUT failed: ${response.status}`);
        throw new Error(`PUT failed: ${response.status}`);
    }

    return response.json();
}

async function toggleDone(csfr, lineNumber) {
    localStorage.setItem("scrollY", window.scrollY);

    await putLine(csfr, lineNumber, { "action": "toggle", "key": "done" });

    location.reload();
}

async function openEdit(csfr, lineNumber) {
    const li = document.getElementById(`task-${lineNumber}`);
    if (!li) return;

    // Hide existing content
    Array.from(li.children).forEach(el => el.style.display = "none");

    // Fetch current task text
    let taskText = "";
    try {
        const data = await getLine(csfr, lineNumber);
        taskText = data.task || "";
    } catch (err) {
        console.error("Failed to fetch task:", err);
        return;
    }

    // Create textarea
    const emptyDiv = document.createElement("div");
    const textarea = document.createElement("textarea");
    textarea.value = taskText
    li.appendChild(emptyDiv);
    li.appendChild(textarea);
    textarea.focus();
    localStorage.setItem("scrollY", window.scrollY);

    // On blur -> save & reload
    textarea.addEventListener("blur", async () => {
        try {
            await putLine(csfr, lineNumber, { "action": "edit", "key": "line", "value": textarea.value.replace(/\r?\n|\r/g, "") });
            location.reload();
        } catch (err) {
            console.error("Failed to save:", err);
            textarea.style.borderColor = "red";
        }
    });

}

async function postLine(csfr, lineNumber, data) {
    const response = await fetch(`${API_BASE}/${lineNumber}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            'X-CSRF-TOKEN': csfr
        },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        showErrorDialog(`POST failed: ${response.status}`);
        throw new Error(`POST failed: ${response.status}`);
    }
    return response.json();
}

async function deleteLine(csfr, lineNumber) {

    localStorage.setItem("scrollY", window.scrollY);

    const response = await fetch(`${API_BASE}/${lineNumber}`, {
        method: "DELETE",
        headers: {
            'X-CSRF-TOKEN': csfr
        }
    });
    if (!response.ok) {
        showErrorDialog(`DELETE failed: ${response.status}`);
        throw new Error(`DELETE failed: ${response.status}`);
    }

    location.reload();

    return response.json();
}
