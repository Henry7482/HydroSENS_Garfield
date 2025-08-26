export interface FormDataLike {
  append(name: string, value: string | Blob, fileName?: string): void;
}