import { fetchMe, login, signup } from "./api.js";
import { ROUTES } from "./config.js";
import { clearSession, getToken, setCurrentUser, setToken } from "./storage.js";

const form = document.querySelector("[data-auth-form]");
const feedback = document.querySelector("#auth-feedback");
const submitButton = document.querySelector("#auth-submit");
const mode = form?.dataset.mode || "login";

function setFeedback(message, type = "error") {
    if (!feedback) {
        return;
    }

    if (!message) {
        feedback.hidden = true;
        feedback.textContent = "";
        feedback.dataset.type = "";
        return;
    }

    feedback.hidden = false;
    feedback.textContent = message;
    feedback.dataset.type = type;
}

function setPending(isPending) {
    if (!form || !submitButton) {
        return;
    }

    Array.from(form.elements).forEach((element) => {
        element.disabled = isPending;
    });

    submitButton.textContent = isPending
        ? (mode === "signup" ? "Creating Account..." : "Signing In...")
        : (mode === "signup" ? "Create Account" : "Sign In");
}

async function redirectIfSessionExists() {
    const token = getToken();
    if (!token) {
        return;
    }

    try {
        const currentUser = await fetchMe(token);
        setCurrentUser(currentUser);
        window.location.replace(ROUTES.app);
    } catch (_error) {
        clearSession();
    }
}

async function handleSubmit(event) {
    event.preventDefault();
    if (!form) {
        return;
    }

    const formData = new FormData(form);
    const email = String(formData.get("email") || "").trim();
    const password = String(formData.get("password") || "");

    setFeedback("");
    setPending(true);

    try {
        if (mode === "signup") {
            await signup({
                full_name: String(formData.get("full_name") || "").trim(),
                email,
                password,
                role: String(formData.get("role") || "doctor"),
            });
        }

        const authPayload = await login({ email, password });
        setToken(authPayload.access_token);

        const currentUser = await fetchMe(authPayload.access_token);
        setCurrentUser(currentUser);

        window.location.replace(ROUTES.app);
    } catch (error) {
        setFeedback(error.message || "Authentication failed.");
        setPending(false);
    }
}

redirectIfSessionExists();

if (form) {
    form.addEventListener("submit", handleSubmit);
}
