const PAGES_CODES_URL = "https://carrotboss271-hash.github.io/Delta-Daily-News/codes.json";
const WORKFLOW_URL = "https://github.com/carrotboss271-hash/Delta-Daily-News/actions/workflows/update-codes.yml";
const DISPATCH_URL = "https://api.github.com/repos/carrotboss271-hash/Delta-Daily-News/actions/workflows/update-codes.yml/dispatches";
const EXPECTED_MAP_IDS = ["zero-dam", "longbow-creek", "buckshot", "space-station", "tide-prison", "az3"];
const ISO_TIMESTAMP = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/;
const beijingDate = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
});

function hasTodayCodes(data, today) {
    const maps = data?.maps;
    if (!maps || typeof maps !== "object" || Object.keys(maps).length !== EXPECTED_MAP_IDS.length) {
        return false;
    }
    const hasValidMaps = EXPECTED_MAP_IDS.every((id) => {
        const code = maps[id];
        return typeof code === "string" && code.length === 4 && /^[0-9]{4}$/.test(code);
    });
    if (!hasValidMaps) {
        return false;
    }

    const updatedAt = data.updatedAt;
    if (typeof updatedAt !== "string" || !ISO_TIMESTAMP.test(updatedAt)) {
        return false;
    }
    const timestamp = Date.parse(updatedAt);
    return Number.isFinite(timestamp) && beijingDate.format(timestamp) === today;
}

async function inspectPages(now, today) {
    const url = new URL(PAGES_CODES_URL);
    url.searchParams.set("_check", String(now));
    try {
        const response = await fetch(url, {
            cache: "no-store",
            signal: AbortSignal.timeout(15_000),
        });
        if (!response.ok) {
            return `pages-http-${response.status}`;
        }
        return hasTodayCodes(await response.json(), today) ? "current" : "stale-or-invalid";
    } catch {
        return "pages-unreadable";
    }
}

async function dispatchUpdate(token) {
    if (!token) {
        throw new Error("GitHub Actions dispatch secret is missing");
    }
    const response = await fetch(DISPATCH_URL, {
        method: "POST",
        headers: {
            Accept: "application/vnd.github+json",
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2026-03-10",
        },
        body: JSON.stringify({ ref: "master", inputs: { skip_if_today: true } }),
        redirect: "error",
        signal: AbortSignal.timeout(15_000),
    });
    if (!response.ok) {
        throw new Error(`GitHub workflow dispatch returned HTTP ${response.status}`);
    }
    if (response.status === 204) {
        return WORKFLOW_URL;
    }
    const { html_url: runUrl } = await response.json();
    return runUrl ?? WORKFLOW_URL;
}

export default {
    async scheduled(_controller, env) {
        const now = Date.now();
        const today = beijingDate.format(now);
        const pages = await inspectPages(now, today);
        if (pages === "current") {
            console.log({ action: "skip", today, pages });
            return;
        }

        try {
            const runUrl = await dispatchUpdate(env.GITHUB_ACTIONS_TOKEN);
            console.log({ action: "dispatch", today, pages, runUrl });
        } catch (error) {
            console.error({ action: "dispatch-failed", today, pages, error: error.message });
            throw error;
        }
    },
};
