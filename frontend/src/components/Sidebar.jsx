import { NavLink, useNavigate } from "react-router-dom";
import {api,clearSession,getSession} from "../api";
const groups=[
 ["OPERATIONS",[["/app","▣","Command Center"],["/app/demo","▶","Guided Demo"],["/app/fleet","▤","Fleet Operations"],["/app/digital-twin","◈","Live Digital Twin"]]],
 ["INTELLIGENCE",[["/app/causal","⚡","Causal Intelligence"],["/app/predictive","⌁","Predictive Analytics"],["/app/decision","◇","Decision Engine"],["/app/interventions","↗","Interventions"]]],
 ["DATA & GOVERNANCE",[["/app/traceability","⬡","Ore Traceability"],["/app/incidents","☷","Incident History"],["/app/data-sources","⇅","Data Sources"],["/app/vision","◉","Vision Intelligence"]]],
];
export default function Sidebar(){const nav=useNavigate();return <aside className="sidebar">
 <div className="sidebar-brand"><div className="sidebar-logo">M</div><div><h1>MINEMIND</h1><p>OPERATIONS AI</p></div></div>
 {groups.map(([title,items])=><div key={title} className="nav-group"><div className="sidebar-section-title">{title}</div><nav className="sidebar-nav">{items.map(([path,icon,label])=><NavLink key={path} to={path} end={path==="/app"} className={({isActive})=>isActive?"sidebar-link active":"sidebar-link"}><span className="sidebar-icon">{icon}</span><span>{label}</span></NavLink>)}</nav></div>)}
 <div className="sidebar-footer"><NavLink to="/app/settings" className="sidebar-link"><span className="sidebar-icon">⚙</span>Settings</NavLink><div className="system-status"><span className="status-dot"></span><div><strong>System Online</strong><p>{getSession()?.workspace?.name||"Mine Workspace"}</p></div></div><button className="logout-btn" onClick={async()=>{try{await api("/auth/logout",{method:"POST"})}catch{}clearSession();nav("/")}}>Sign out</button></div>
 </aside>}
