import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { BookOptionsProvider } from "./context/BookOptions";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BookOptionsProvider>
      <App />
    </BookOptionsProvider>
  </StrictMode>,
);
