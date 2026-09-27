// The whole site renders client-side. A crawler that does not run JS sees an empty #root.
const routes = {"/": "Quartzline: log search for small teams"};
document.getElementById("root").innerHTML = "<main><h1>" + (routes[location.pathname] || "Quartzline") + "</h1></main>";
