import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./style.css";

const root = document.getElementById("root");
if (root) {
  ReactDOM.createRoot(root).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
} else {
  document.body.innerHTML =
    '<h2 style="color:red">Root element not found!</h2>';
}
