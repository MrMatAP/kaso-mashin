// Composables
import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    component: () => import("@/layouts/default/Default.vue"),
    children: [
      {
        path: "/",
        component: () => import("@/pages/Landing.vue"),
      },
      {
        path: "/instances",
        name: "Instances",
        component: () => import("@/pages/Instances.vue"),
      },
      {
        path: "/instances/:uid",
        name: "InstanceDetail",
        component: () => import("@/pages/InstanceDetail.vue"),
      },
      {
        path: "/instances/?create",
        name: "InstanceCreate",
        component: () => import("@/pages/InstanceDetail.vue"),
      },
      {
        path: "/identities",
        name: "Identities",
        component: () => import("@/pages/Identities.vue"),
      },
      {
        path: "/identities/:uid",
        name: "IdentityDetail",
        component: () => import("@/pages/IdentityDetail.vue"),
      },
      {
        path: "/identities/?create",
        name: "IdentityCreate",
        component: () => import("@/pages/IdentityDetail.vue"),
      },
      {
        path: "/networks",
        name: "Networks",
        component: () => import("@/pages/Networks.vue"),
      },
      {
        path: "/networks/:uid",
        name: "NetworkDetail",
        component: () => import("@/pages/NetworkDetail.vue"),
      },
      {
        path: "/networks/?create",
        name: "NetworkCreate",
        component: () => import("@/pages/NetworkDetail.vue"),
      },
      {
        path: "/images",
        name: "Images",
        component: () => import("@/pages/Images.vue"),
      },
      {
        path: "/images/:uid",
        name: "ImageDetail",
        component: () => import("@/pages/ImageDetail.vue"),
      },
      {
        path: "/images/?create",
        name: "ImageCreate",
        component: () => import("@/pages/ImageDetail.vue"),
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
