import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";

const nativeFetch=window.fetch.bind(window);
window.fetch=(input,init={})=>{const url=typeof input==="string"?input:input.url;const apiBase=import.meta.env.VITE_API_URL||"http://127.0.0.1:8000";if(url.startsWith(apiBase)){let session=null;try{session=JSON.parse(localStorage.getItem("minemind_session")||"null")}catch{}if(session?.token){const headers=new Headers(init.headers||{});if(!headers.has("Authorization"))headers.set("Authorization",`Bearer ${session.token}`);return nativeFetch(input,{...init,headers})}}return nativeFetch(input,init)};

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);