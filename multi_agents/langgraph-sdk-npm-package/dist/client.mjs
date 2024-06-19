import { AsyncCaller } from "./utils/async_caller.mjs";
import { createParser } from "eventsource-parser";
import { IterableReadableStream } from "./utils/stream.mjs";
class BaseClient {
    constructor(config) {
        Object.defineProperty(this, "asyncCaller", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "timeoutMs", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "apiUrl", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "defaultHeaders", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        this.asyncCaller = new AsyncCaller({
            maxRetries: 4,
            maxConcurrency: 4,
            ...config?.callerOptions,
        });
        this.timeoutMs = config?.timeoutMs || 12_000;
        this.apiUrl = config?.apiUrl || "http://localhost:8123";
        this.defaultHeaders = config?.defaultHeaders || {};
    }
    prepareFetchOptions(path, options) {
        const mutatedOptions = {
            ...options,
            headers: { ...this.defaultHeaders, ...options?.headers },
        };
        if (mutatedOptions.json) {
            mutatedOptions.body = JSON.stringify(mutatedOptions.json);
            mutatedOptions.headers = {
                ...mutatedOptions.headers,
                "Content-Type": "application/json",
            };
            delete mutatedOptions.json;
        }
        const targetUrl = new URL(`${this.apiUrl}${path}`);
        if (mutatedOptions.params) {
            for (const [key, value] of Object.entries(mutatedOptions.params)) {
                if (value == null)
                    continue;
                let strValue = typeof value === "string" || typeof value === "number"
                    ? value.toString()
                    : JSON.stringify(value);
                targetUrl.searchParams.append(key, strValue);
            }
            delete mutatedOptions.params;
        }
        return [targetUrl, mutatedOptions];
    }
    async fetch(path, options) {
        const response = await this.asyncCaller.fetch(...this.prepareFetchOptions(path, options));
        if (response.status === 202 || response.status === 204) {
            return undefined;
        }
        return response.json();
    }
}
class AssistantsClient extends BaseClient {
    /**
     * Get an assistant by ID.
     *
     * @param assistantId The ID of the assistant.
     * @returns Assistant
     */
    async get(assistantId) {
        return this.fetch(`/assistants/${assistantId}`);
    }
    /**
     * Get the JSON representation of the graph assigned to a runnable
     * @param assistantId The ID of the assistant.
     * @returns Serialized graph
     */
    async getGraph(assistantId) {
        return this.fetch(`/assistants/${assistantId}/graph`);
    }
    /**
     * Get the state and config schema of the graph assigned to a runnable
     * @param assistantId The ID of the assistant.
     * @returns Graph schema
     */
    async getSchemas(assistantId) {
        return this.fetch(`/assistants/${assistantId}/schemas`);
    }
    /**
     * Create a new assistant.
     * @param payload Payload for creating an assistant.
     * @returns The created assistant.
     */
    async create(payload) {
        return this.fetch("/assistants", {
            method: "POST",
            json: {
                graph_id: payload.graphId,
                config: payload.config,
                metadata: payload.metadata,
            },
        });
    }
    /**
     * Update an assistant.
     * @param assistantId ID of the assistant.
     * @param payload Payload for updating the assistant.
     * @returns The updated assistant.
     */
    async update(assistantId, payload) {
        return this.fetch(`/assistants/${assistantId}`, {
            method: "PATCH",
            json: {
                graph_id: payload.graphId,
                config: payload.config,
                metadata: payload.metadata,
            },
        });
    }
    /**
     * Delete an assistant.
     *
     * @param assistantId ID of the assistant.
     */
    async delete(assistantId) {
        return this.fetch(`/assistants/${assistantId}`, {
            method: "DELETE",
        });
    }
    /**
     * List assistants.
     * @param query Query options.
     * @returns List of assistants.
     */
    async search(query) {
        return this.fetch("/assistants/search", {
            method: "POST",
            json: {
                metadata: query?.metadata ?? undefined,
                limit: query?.limit ?? 10,
                offset: query?.offset ?? 0,
            },
        });
    }
}
class ThreadsClient extends BaseClient {
    /**
     * Get a thread by ID.
     *
     * @param threadId ID of the thread.
     * @returns The thread.
     */
    async get(threadId) {
        return this.fetch(`/threads/${threadId}`);
    }
    /**
     * Create a new thread.
     *
     * @param payload Payload for creating a thread.
     * @returns The created thread.
     */
    async create(payload) {
        return this.fetch(`/threads`, {
            method: "POST",
            json: { metadata: payload?.metadata },
        });
    }
    /**
     * Update a thread.
     *
     * @param threadId ID of the thread.
     * @param payload Payload for updating the thread.
     * @returns The updated thread.
     */
    async update(threadId, payload) {
        return this.fetch(`/threads/${threadId}`, {
            method: "PATCH",
            json: { metadata: payload?.metadata },
        });
    }
    /**
     * Delete a thread.
     *
     * @param threadId ID of the thread.
     */
    async delete(threadId) {
        return this.fetch(`/threads/${threadId}`, {
            method: "DELETE",
        });
    }
    /**
     * List threads
     *
     * @param query Query options
     * @returns List of threads
     */
    async search(query) {
        return this.fetch("/threads/search", {
            method: "POST",
            json: {
                metadata: query?.metadata ?? undefined,
                limit: query?.limit ?? 10,
                offset: query?.offset ?? 0,
            },
        });
    }
    /**
     * Get state for a thread.
     *
     * @param threadId ID of the thread.
     * @returns Thread state.
     */
    async getState(threadId, checkpointId) {
        return this.fetch(checkpointId != null
            ? `/threads/${threadId}/state/${checkpointId}`
            : `/threads/${threadId}/state`);
    }
    /**
     * Add state to a thread.
     *
     * @param threadId The ID of the thread.
     * @returns
     */
    async updateState(threadId, options) {
        return this.fetch(`/threads/${threadId}/state`, {
            method: "POST",
            json: {
                values: options.values,
                checkpoint_id: options.checkpointId,
                as_node: options?.asNode,
            },
        });
    }
    /**
     * Patch the metadata of a thread.
     *
     * @param threadIdOrConfig Thread ID or config to patch the state of.
     * @param metadata Metadata to patch the state with.
     */
    async patchState(threadIdOrConfig, metadata) {
        let threadId;
        if (typeof threadIdOrConfig !== "string") {
            if (typeof threadIdOrConfig.configurable.thread_id !== "string") {
                throw new Error("Thread ID is required when updating state with a config.");
            }
            threadId = threadIdOrConfig.configurable.thread_id;
        }
        else {
            threadId = threadIdOrConfig;
        }
        return this.fetch(`/threads/${threadId}/state`, {
            method: "PATCH",
            json: { metadata: metadata },
        });
    }
    /**
     * Get all past states for a thread.
     *
     * @param threadId ID of the thread.
     * @param options Additional options.
     * @returns List of thread states.
     */
    async getHistory(threadId, options) {
        return this.fetch(`/threads/${threadId}/history`, {
            method: "POST",
            json: {
                limit: options?.limit ?? 10,
                before: options?.before,
                metadata: options?.metadata,
            },
        });
    }
}
class RunsClient extends BaseClient {
    /**
     * Create a run and stream the results.
     *
     * @param threadId The ID of the thread.
     * @param assistantId Assistant ID to use for this run.
     * @param payload Payload for creating a run.
     */
    async *stream(threadId, assistantId, payload) {
        const json = {
            input: payload?.input,
            config: payload?.config,
            metadata: payload?.metadata,
            stream_mode: payload?.streamMode,
            feedback_keys: payload?.feedbackKeys,
            assistant_id: assistantId,
            interrupt_before: payload?.interruptBefore,
            interrupt_after: payload?.interruptAfter,
        };
        if (payload?.multitaskStrategy != null) {
            json["multitask_strategy"] = payload?.multitaskStrategy;
        }
        const endpoint = threadId == null ? `/runs/stream` : `/threads/${threadId}/runs/stream`;
        const response = await this.asyncCaller.fetch(...this.prepareFetchOptions(endpoint, {
            method: "POST",
            json,
            signal: payload?.signal,
        }));
        let parser;
        const textDecoder = new TextDecoder();
        const stream = (response.body || new ReadableStream({ start: (ctrl) => ctrl.close() })).pipeThrough(new TransformStream({
            async start(ctrl) {
                parser = createParser((event) => {
                    if ((payload?.signal && payload.signal.aborted) ||
                        (event.type === "event" && event.data === "[DONE]")) {
                        ctrl.terminate();
                        return;
                    }
                    if ("data" in event) {
                        ctrl.enqueue({
                            event: event.event ?? "message",
                            data: JSON.parse(event.data),
                        });
                    }
                });
            },
            async transform(chunk) {
                parser.feed(textDecoder.decode(chunk));
            },
        }));
        yield* IterableReadableStream.fromReadableStream(stream);
    }
    /**
     * Create a run.
     *
     * @param threadId The ID of the thread.
     * @param assistantId Assistant ID to use for this run.
     * @param payload Payload for creating a run.
     * @returns The created run.
     */
    async create(threadId, assistantId, payload) {
        const json = {
            input: payload?.input,
            config: payload?.config,
            metadata: payload?.metadata,
            assistant_id: assistantId,
            interrupt_before: payload?.interruptBefore,
            interrupt_after: payload?.interruptAfter,
            webhook: payload?.webhook,
        };
        if (payload?.multitaskStrategy != null) {
            json["multitask_strategy"] = payload?.multitaskStrategy;
        }
        return this.fetch(`/threads/${threadId}/runs`, {
            method: "POST",
            json,
            signal: payload?.signal,
        });
    }
    /**
     * Create a run and wait for it to complete.
     *
     * @param threadId The ID of the thread.
     * @param assistantId Assistant ID to use for this run.
     * @param payload Payload for creating a run.
     * @returns The last values chunk of the thread.
     */
    async wait(threadId, assistantId, payload) {
        const json = {
            input: payload?.input,
            config: payload?.config,
            metadata: payload?.metadata,
            assistant_id: assistantId,
            interrupt_before: payload?.interruptBefore,
            interrupt_after: payload?.interruptAfter,
        };
        if (payload?.multitaskStrategy != null) {
            json["multitask_strategy"] = payload?.multitaskStrategy;
        }
        const endpoint = threadId == null ? `/runs/wait` : `/threads/${threadId}/runs/wait`;
        return this.fetch(endpoint, {
            method: "POST",
            json,
            signal: payload?.signal,
        });
    }
    /**
     * List all runs for a thread.
     *
     * @param threadId The ID of the thread.
     * @param options Filtering and pagination options.
     * @returns List of runs.
     */
    async list(threadId, options) {
        return this.fetch(`/threads/${threadId}/runs`, {
            params: {
                limit: options?.limit ?? 10,
                offset: options?.offset ?? 0,
            },
        });
    }
    /**
     * Get a run by ID.
     *
     * @param threadId The ID of the thread.
     * @param runId The ID of the run.
     * @returns The run.
     */
    async get(threadId, runId) {
        return this.fetch(`/threads/${threadId}/runs/${runId}`);
    }
    /**
     * Cancel a run.
     *
     * @param threadId The ID of the thread.
     * @param runId The ID of the run.
     * @param wait Whether to block when canceling
     * @returns
     */
    async cancel(threadId, runId, wait = false) {
        return this.fetch(`/threads/${threadId}/runs/${runId}/cancel`, {
            method: "POST",
            params: {
                wait: wait ? "1" : "0",
            },
        });
    }
    /**
     * Block until a run is done.
     *
     * @param threadId The ID of the thread.
     * @param runId The ID of the run.
     * @returns
     */
    async join(threadId, runId) {
        return this.fetch(`/threads/${threadId}/runs/${runId}/join`);
    }
    /**
     * Delete a run.
     *
     * @param threadId The ID of the thread.
     * @param runId The ID of the run.
     * @returns
     */
    async delete(threadId, runId) {
        return this.fetch(`/threads/${threadId}/runs/${runId}`, {
            method: "DELETE",
        });
    }
}
export class Client {
    constructor(config) {
        /**
         * The client for interacting with assistants.
         */
        Object.defineProperty(this, "assistants", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        /**
         * The client for interacting with threads.
         */
        Object.defineProperty(this, "threads", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        /**
         * The client for interacting with runs.
         */
        Object.defineProperty(this, "runs", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        this.assistants = new AssistantsClient(config);
        this.threads = new ThreadsClient(config);
        this.runs = new RunsClient(config);
    }
}
