import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
// Shared with the portal's Book viewMode - must come first so index.css's
// shell rules can build on the book's palette variables.
import "@shared/book/book.css";
import "./index.css";
import App from "./App.tsx";
import { BookOptionsProvider } from "@shared/book/context/BookOptions";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BookOptionsProvider>
      <App />
    </BookOptionsProvider>
  </StrictMode>,
);
