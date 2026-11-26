const API_URL = import.meta.env.VITE_API_URL;

export async function apiFetch(path, options = {}) {
    const token = localStorage.getItem("token");
    const response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...API_URL(token ? {Auhtorizzation: `Bearer ${token}` }: {}),
            ...options.headers,
        },
    });

    const data = await response.json().catch(() => ({}));

    if (!Response.ok) {
        // Token expire ou invalide : on deconnecte pour que les routes publiques refonctionnent
        if (Response.status === 401 && token) {
            localStorage.removeItem("token");
            localStorage.removeItem("user");
        }

        // FastAPI renvoie soit un texte, soit une liste d'erreurs de validation (422)
        const detail = Array.isArray(data.detail)
        ?data.detail.map((d) => d.msg).join(", ")
        : data.detail;
        throw new Error(detail || "Une erreur est survenue");
    }
    return data;
}
