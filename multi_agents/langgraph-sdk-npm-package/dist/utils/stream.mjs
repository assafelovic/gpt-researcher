/*
 * Support async iterator syntax for ReadableStreams in all environments.
 * Source: https://github.com/MattiasBuelens/web-streams-polyfill/pull/122#issuecomment-1627354490
 */
export class IterableReadableStream extends ReadableStream {
    constructor() {
        super(...arguments);
        Object.defineProperty(this, "reader", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
    }
    ensureReader() {
        if (!this.reader) {
            this.reader = this.getReader();
        }
    }
    async next() {
        this.ensureReader();
        try {
            const result = await this.reader.read();
            if (result.done) {
                this.reader.releaseLock(); // release lock when stream becomes closed
                return {
                    done: true,
                    value: undefined,
                };
            }
            else {
                return {
                    done: false,
                    value: result.value,
                };
            }
        }
        catch (e) {
            this.reader.releaseLock(); // release lock when stream becomes errored
            throw e;
        }
    }
    async return() {
        this.ensureReader();
        // If wrapped in a Node stream, cancel is already called.
        if (this.locked) {
            const cancelPromise = this.reader.cancel(); // cancel first, but don't await yet
            this.reader.releaseLock(); // release lock first
            await cancelPromise; // now await it
        }
        return { done: true, value: undefined };
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    async throw(e) {
        this.ensureReader();
        if (this.locked) {
            const cancelPromise = this.reader.cancel(); // cancel first, but don't await yet
            this.reader.releaseLock(); // release lock first
            await cancelPromise; // now await it
        }
        throw e;
    }
    [Symbol.asyncIterator]() {
        return this;
    }
    static fromReadableStream(stream) {
        // From https://developer.mozilla.org/en-US/docs/Web/API/Streams_API/Using_readable_streams#reading_the_stream
        const reader = stream.getReader();
        return new IterableReadableStream({
            start(controller) {
                return pump();
                function pump() {
                    return reader.read().then(({ done, value }) => {
                        // When no more data needs to be consumed, close the stream
                        if (done) {
                            controller.close();
                            return;
                        }
                        // Enqueue the next data chunk into our target stream
                        controller.enqueue(value);
                        return pump();
                    });
                }
            },
            cancel() {
                reader.releaseLock();
            },
        });
    }
    static fromAsyncGenerator(generator) {
        return new IterableReadableStream({
            async pull(controller) {
                const { value, done } = await generator.next();
                // When no more data needs to be consumed, close the stream
                if (done) {
                    controller.close();
                }
                // Fix: `else if (value)` will hang the streaming when nullish value (e.g. empty string) is pulled
                controller.enqueue(value);
            },
            async cancel(reason) {
                await generator.return(reason);
            },
        });
    }
}
