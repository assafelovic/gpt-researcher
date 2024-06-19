import { Assistant, AssistantGraph, Config, DefaultValues, GraphSchema, Metadata, Run, Thread, ThreadState } from "./schema.js";
import { AsyncCaller, AsyncCallerParams } from "./utils/async_caller.mjs";
import { RunsCreatePayload, RunsStreamPayload, RunsWaitPayload, StreamEvent } from "./types.mjs";
interface ClientConfig {
    apiUrl?: string;
    callerOptions?: AsyncCallerParams;
    timeoutMs?: number;
    defaultHeaders?: Record<string, string | null | undefined>;
}
declare class BaseClient {
    protected asyncCaller: AsyncCaller;
    protected timeoutMs: number;
    protected apiUrl: string;
    protected defaultHeaders: Record<string, string | null | undefined>;
    constructor(config?: ClientConfig);
    protected prepareFetchOptions(path: string, options?: RequestInit & {
        json?: unknown;
        params?: Record<string, unknown>;
    }): [url: URL, init: RequestInit];
    protected fetch<T>(path: string, options?: RequestInit & {
        json?: unknown;
        params?: Record<string, unknown>;
    }): Promise<T>;
}
declare class AssistantsClient extends BaseClient {
    /**
     * Get an assistant by ID.
     *
     * @param assistantId The ID of the assistant.
     * @returns Assistant
     */
    get(assistantId: string): Promise<Assistant>;
    /**
     * Get the JSON representation of the graph assigned to a runnable
     * @param assistantId The ID of the assistant.
     * @returns Serialized graph
     */
    getGraph(assistantId: string): Promise<AssistantGraph>;
    /**
     * Get the state and config schema of the graph assigned to a runnable
     * @param assistantId The ID of the assistant.
     * @returns Graph schema
     */
    getSchemas(assistantId: string): Promise<GraphSchema>;
    /**
     * Create a new assistant.
     * @param payload Payload for creating an assistant.
     * @returns The created assistant.
     */
    create(payload: {
        graphId: string;
        config?: Config;
        metadata?: Metadata;
    }): Promise<Assistant>;
    /**
     * Update an assistant.
     * @param assistantId ID of the assistant.
     * @param payload Payload for updating the assistant.
     * @returns The updated assistant.
     */
    update(assistantId: string, payload: {
        graphId: string;
        config?: Config;
        metadata?: Metadata;
    }): Promise<Assistant>;
    /**
     * Delete an assistant.
     *
     * @param assistantId ID of the assistant.
     */
    delete(assistantId: string): Promise<void>;
    /**
     * List assistants.
     * @param query Query options.
     * @returns List of assistants.
     */
    search(query?: {
        metadata?: Metadata;
        limit?: number;
        offset?: number;
    }): Promise<Assistant[]>;
}
declare class ThreadsClient extends BaseClient {
    /**
     * Get a thread by ID.
     *
     * @param threadId ID of the thread.
     * @returns The thread.
     */
    get(threadId: string): Promise<Thread>;
    /**
     * Create a new thread.
     *
     * @param payload Payload for creating a thread.
     * @returns The created thread.
     */
    create(payload?: {
        /**
         * Metadata for the thread.
         */
        metadata?: Metadata;
    }): Promise<Thread>;
    /**
     * Update a thread.
     *
     * @param threadId ID of the thread.
     * @param payload Payload for updating the thread.
     * @returns The updated thread.
     */
    update(threadId: string, payload?: {
        /**
         * Metadata for the thread.
         */
        metadata?: Metadata;
    }): Promise<Thread>;
    /**
     * Delete a thread.
     *
     * @param threadId ID of the thread.
     */
    delete(threadId: string): Promise<void>;
    /**
     * List threads
     *
     * @param query Query options
     * @returns List of threads
     */
    search(query?: {
        /**
         * Metadata to filter threads by.
         */
        metadata?: Metadata;
        /**
         * Maximum number of threads to return.
         * Defaults to 10
         */
        limit?: number;
        /**
         * Offset to start from.
         */
        offset?: number;
    }): Promise<Thread[]>;
    /**
     * Get state for a thread.
     *
     * @param threadId ID of the thread.
     * @returns Thread state.
     */
    getState<ValuesType = DefaultValues>(threadId: string, checkpointId?: string): Promise<ThreadState<ValuesType>>;
    /**
     * Add state to a thread.
     *
     * @param threadId The ID of the thread.
     * @returns
     */
    updateState<ValuesType = DefaultValues>(threadId: string, options: {
        values: ValuesType;
        checkpointId?: string;
        asNode?: string;
    }): Promise<void>;
    /**
     * Patch the metadata of a thread.
     *
     * @param threadIdOrConfig Thread ID or config to patch the state of.
     * @param metadata Metadata to patch the state with.
     */
    patchState(threadIdOrConfig: string | Config, metadata: Metadata): Promise<void>;
    /**
     * Get all past states for a thread.
     *
     * @param threadId ID of the thread.
     * @param options Additional options.
     * @returns List of thread states.
     */
    getHistory<ValuesType = DefaultValues>(threadId: string, options?: {
        limit?: number;
        before?: Config;
        metadata?: Metadata;
    }): Promise<ThreadState<ValuesType>[]>;
}
declare class RunsClient extends BaseClient {
    stream(threadId: null, assistantId: string, payload?: Omit<RunsStreamPayload, "multitaskStrategy">): AsyncGenerator<{
        event: StreamEvent;
        data: any;
    }>;
    stream(threadId: string, assistantId: string, payload?: RunsStreamPayload): AsyncGenerator<{
        event: StreamEvent;
        data: any;
    }>;
    /**
     * Create a run.
     *
     * @param threadId The ID of the thread.
     * @param assistantId Assistant ID to use for this run.
     * @param payload Payload for creating a run.
     * @returns The created run.
     */
    create(threadId: string, assistantId: string, payload?: RunsCreatePayload): Promise<Run>;
    wait(threadId: null, assistantId: string, payload?: Omit<RunsWaitPayload, "multitaskStrategy">): Promise<ThreadState["values"]>;
    wait(threadId: string, assistantId: string, payload?: RunsWaitPayload): Promise<ThreadState["values"]>;
    /**
     * List all runs for a thread.
     *
     * @param threadId The ID of the thread.
     * @param options Filtering and pagination options.
     * @returns List of runs.
     */
    list(threadId: string, options?: {
        /**
         * Maximum number of runs to return.
         * Defaults to 10
         */
        limit?: number;
        /**
         * Offset to start from.
         * Defaults to 0.
         */
        offset?: number;
    }): Promise<Run[]>;
    /**
     * Get a run by ID.
     *
     * @param threadId The ID of the thread.
     * @param runId The ID of the run.
     * @returns The run.
     */
    get(threadId: string, runId: string): Promise<Run>;
    /**
     * Cancel a run.
     *
     * @param threadId The ID of the thread.
     * @param runId The ID of the run.
     * @param wait Whether to block when canceling
     * @returns
     */
    cancel(threadId: string, runId: string, wait?: boolean): Promise<void>;
    /**
     * Block until a run is done.
     *
     * @param threadId The ID of the thread.
     * @param runId The ID of the run.
     * @returns
     */
    join(threadId: string, runId: string): Promise<void>;
    /**
     * Delete a run.
     *
     * @param threadId The ID of the thread.
     * @param runId The ID of the run.
     * @returns
     */
    delete(threadId: string, runId: string): Promise<void>;
}
export declare class Client {
    /**
     * The client for interacting with assistants.
     */
    assistants: AssistantsClient;
    /**
     * The client for interacting with threads.
     */
    threads: ThreadsClient;
    /**
     * The client for interacting with runs.
     */
    runs: RunsClient;
    constructor(config?: ClientConfig);
}
export {};
