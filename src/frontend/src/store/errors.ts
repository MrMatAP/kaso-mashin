import { defineStore } from "pinia";

export class ErrorSchema {
  msg: string = "An unknown error has occurred";
}

export const useErrorStore = defineStore("errors", {
  state: () => ({
    errors: [] as ErrorSchema[],
  }),
});
