export const API=import.meta.env.VITE_API_URL||"http://127.0.0.1:8000";
export function getSession(){try{return JSON.parse(localStorage.getItem("minemind_session")||"null")}catch{return null}}
export function saveSession(s){localStorage.setItem("minemind_session",JSON.stringify(s));window.dispatchEvent(new Event("minemind-session"))}
export function clearSession(){localStorage.removeItem("minemind_session");window.dispatchEvent(new Event("minemind-session"))}
export async function api(path,options={}){const s=getSession();const headers={...(options.headers||{})};if(s?.token)headers.Authorization=`Bearer ${s.token}`;if(options.body&&!headers["Content-Type"])headers["Content-Type"]="application/json";const r=await fetch(`${API}${path}`,{...options,headers});if(r.status===401){clearSession();if(location.pathname.startsWith('/app'))location.href='/login';throw new Error('Session expired')}const data=await r.json().catch(()=>({}));if(!r.ok)throw new Error(data.detail||data.message||`Request failed (${r.status})`);return data}

export async function apiFetch(path,options={}){const s=getSession();const headers={...(options.headers||{})};if(s?.token)headers.Authorization=`Bearer ${s.token}`;const r=await fetch(`${API}${path}`,{...options,headers});if(r.status===401){clearSession();if(location.pathname.startsWith('/app'))location.href='/login'}return r}
