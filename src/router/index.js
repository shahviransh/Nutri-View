import { createRouter, createWebHistory } from "vue-router";
import Project from "../pages/Project.vue";
import Graph from "../pages/Graph.vue";
import Map from "../pages/Map.vue";
import Help from "../pages/Help.vue";
import Converter from "../pages/Converter.vue";

const routes = [
  {
    path: "/",
    component: Project,
  },
  {
    path: "/project",
    name: "Project",
    component: Project,
  },
  {
    path: "/table",
    name: "Table",
    component: Project,
  },
  {
    path: "/graph",
    name: "Graph",
    component: Graph,
  },
  {
    path: "/map",
    name: "Map",
    component: Map,
  },
  {
    path: "/converter",
    name: "Converter",
    component: Converter,
  },
  {
    path: "/help",
    name: "Help",
    component: Help,
  },
];

const router = createRouter({
  history: createWebHistory("/"), // Use default web history
  routes,
});

export default router;