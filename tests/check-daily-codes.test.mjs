import assert from "node:assert/strict";
import { test } from "node:test";
import worker from "../cloudflare/check-daily-codes.mjs";

const maps = {
    "zero-dam": "0123",
    "longbow-creek": "1234",
    buckshot: "2345",
    "space-station": "3456",
    "tide-prison": "4567",
    az3: "5678",
};
const now = new Date("2026-11-24T20:25:00Z");
const currentCodes = { updatedAt: "2026-11-25T04:17:00+08:00", maps };
const env = { GITHUB_ACTIONS_TOKEN: "test-token" };
const runUrl = "https://github.com/carrotboss271-hash/Delta-Daily-News/actions/runs/1";

function mockCheck(t, pagesResponse) {
    t.mock.timers.enable({ apis: ["Date"], now });
    const log = t.mock.method(console, "log", () => {});
    const sendRequest = t.mock.method(globalThis, "fetch", async (url, options) => {
        if (options.method === "POST") {
            return Response.json({ html_url: runUrl });
        }
        return pagesResponse();
    });
    return { log, sendRequest };
}

test("checks the Beijing date and skips dispatch when Pages has all six codes", async (t) => {
    const { log, sendRequest } = mockCheck(t, () => Response.json(currentCodes));

    await worker.scheduled({}, {});

    assert.equal(sendRequest.mock.callCount(), 1);
    const [url, options] = sendRequest.mock.calls[0].arguments;
    assert.equal(url.searchParams.get("_check"), String(now.getTime()));
    assert.equal(options.cache, "no-store");
    assert.equal(options.headers?.Authorization, undefined);
    assert.deepEqual(log.mock.calls[0].arguments[0], { action: "skip", today: "2026-11-25", pages: "current" });
});

for (const [scenario, pagesResponse, reason] of [
    ["a timestamp that is still yesterday in Beijing", () => Response.json({
        ...currentCodes, updatedAt: "2026-11-25T00:30:00+09:00",
    }), "stale-or-invalid"],
    ["an invalid map code", () => Response.json({ ...currentCodes, maps: { ...maps, az3: "5678\n" } }), "stale-or-invalid"],
    ["a missing map", () => Response.json({ ...currentCodes, maps: { az3: maps.az3 } }), "stale-or-invalid"],
    ["a Pages HTTP error", () => new Response(null, { status: 503 }), "pages-http-503"],
    ["unreadable Pages data", () => new Response("<html>"), "pages-unreadable"],
]) {
    test(`dispatches backup when Pages returns ${scenario}`, async (t) => {
        const { log, sendRequest } = mockCheck(t, pagesResponse);

        await worker.scheduled({}, env);

        assert.equal(sendRequest.mock.callCount(), 2);
        const [url, options] = sendRequest.mock.calls[1].arguments;
        assert.equal(url, "https://api.github.com/repos/carrotboss271-hash/Delta-Daily-News/actions/workflows/update-codes.yml/dispatches");
        assert.equal(options.method, "POST");
        assert.equal(options.headers.Authorization, "Bearer test-token");
        assert.deepEqual(JSON.parse(options.body), { ref: "master", inputs: { skip_if_today: true } });
        assert.deepEqual(log.mock.calls[0].arguments[0], { action: "dispatch", today: "2026-11-25", pages: reason, runUrl });
    });
}

test("marks the scheduled invocation as failed when GitHub rejects dispatch", async (t) => {
    const log = t.mock.method(console, "error", () => {});
    t.mock.method(globalThis, "fetch", async (_url, options) => (
        new Response(null, { status: options.method === "POST" ? 403 : 404 })
    ));

    await assert.rejects(worker.scheduled({}, env), /GitHub workflow dispatch returned HTTP 403/);
    assert.equal(log.mock.calls[0].arguments[0].action, "dispatch-failed");
});
