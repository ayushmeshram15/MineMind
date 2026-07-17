import { useEffect, useState } from "react"; import { useLocation, useNavigate } from "react-router-dom"; import {api} from "../api";
export default function GuidedDemo(){const loc=useLocation(),nav=useNavigate();const [open,setOpen]=useState(()=>localStorage.getItem("mm_demo_hidden")!=="1");const [sim,setSim]=useState(null);const [causal,setCausal]=useState(null);
 useEffect(()=>{const load=()=>Promise.all([api('/simulation/state'),api('/causal/state')]).then(([s,c])=>{setSim(s);setCausal(c)}).catch(()=>{});load();const id=setInterval(load,2000);return()=>clearInterval(id)},[]);
 if(!open)return <button className="demo-reopen" onClick={()=>setOpen(true)}>Demo guide</button>;
 const incident=causal?.active_incident; let title="Start live operations",text="Launch the canonical fleet stream from Command Center.",path="/app",action="Open Command Center";
 if(sim?.status==="RUNNING"&&!incident){title="Watch the operation";text="Fleet is live. Inspect trucks and routes while MineMind monitors degradation.";path="/app/fleet";action="Open Fleet Operations"}
 if(incident){title="Incident detected";text="MineMind has a causal incident. Review propagation, prediction and the recommended action.";path="/app/causal";action="Review Causal Intelligence"}
 return <aside className="guided-demo"><button className="guide-close" onClick={()=>{setOpen(false);localStorage.setItem("mm_demo_hidden","1")}}>×</button><small>GUIDED PRODUCT DEMO</small><strong>{title}</strong><p>{text}</p><button onClick={()=>nav(path)}>{loc.pathname===path?"You are here":action} →</button></aside>}
