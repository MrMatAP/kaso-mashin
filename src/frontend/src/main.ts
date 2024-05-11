/**
 * main.ts
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

import { createApp } from "vue";
import { Quasar, Loading } from "quasar";
import quasarLang from "quasar/lang/en-GB";
import pinia from "@/store";
import router from "@/router";

//
// Icon libraries
import "@quasar/extras/roboto-font-latin-ext/roboto-font-latin-ext.css";
import "@quasar/extras/material-icons/material-icons.css";
import "@quasar/extras/fontawesome-v6/fontawesome-v6.css";

//
// Import Quasar css
import "quasar/src/css/index.sass";

//
// App Root Component

import App from "./App.vue";
const app = createApp(App);
app
  .use(Quasar, {
    plugins: {
      Loading,
    },
    lang: quasarLang,
  })
  .use(pinia)
  .use(router);

app.mount("#app");
