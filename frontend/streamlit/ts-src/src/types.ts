/**
 * Type definitions for the GPT Researcher UI
 */

export interface ResearchSettings {
    query?: string;
    report_type?: string;
    report_format?: string;
    [key: string]: any;
}

export interface ChatMessage {
    content: string;
    isUser: boolean;
}

export interface EventData {
    type: string;
    level?: string;
    message?: string;
    content?: string;
    files?: Record<string, string>;
    base_filename?: string;
    format?: string;
}

export interface FormElements extends HTMLFormControlsCollection {
    query: HTMLInputElement;
    report_type: HTMLSelectElement;
    documents: HTMLInputElement;
}

export interface ResearchForm extends HTMLFormElement {
    elements: FormElements;
} 