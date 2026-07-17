import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";
import { ToastProvider } from "./components/toast";
import { SharedProvider } from "./shared";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ToastProvider>
      <SharedProvider>
        <App />
      </SharedProvider>
    </ToastProvider>
  </StrictMode>
);
