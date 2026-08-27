export function readPrivateFont(id: string, directory?: string): Promise<Buffer>;
export function validatePrivateFonts(options?: { mode?: string; env?: NodeJS.ProcessEnv; directory?: string }): Promise<{status: string; fonts: number}>;
