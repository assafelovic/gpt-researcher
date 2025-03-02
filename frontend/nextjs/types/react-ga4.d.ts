declare module 'react-ga4' {
    export interface InitOptions {
      gaOptions?: any;
      gtagOptions?: any;
      testMode?: boolean;
    }
  
    export function initialize(
      measurementId: string | string[],
      options?: InitOptions
    ): void;
  
    export function event(options: {
      category: string;
      action: string;
      label?: string;
      value?: number;
      nonInteraction?: boolean;
      transport?: 'beacon' | 'xhr' | 'image';
      [key: string]: any;
    }): void;
  
    // Add other methods as needed
    export default {
      initialize,
      event
    };
  }