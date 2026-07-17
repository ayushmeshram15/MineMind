"""MineMind canonical core-operations simulation.

One backend clock owns dispatch, route movement, crusher queues, ore delivery,
crusher buffers and production telemetry. The Digital Twin only renders this state.
"""
from datetime import datetime
import math, random, threading
from mine_state import mine_state, add_causal_event, add_trace_event
from causal_engine import process_fleet_tick

TICK_SECONDS = 1.0
SIMULATION_MINUTES_PER_TICK = 1
ROUTES = {
    "R1": {"pit_id":"P1","dump_id":"C1","capacity":3,"waypoints":[(-40,-30),(-34,-22),(-27,-15),(-22,-6),(-15,2),(-12,12),(-8,22),(-6,30)]},
    "R2": {"pit_id":"P2","dump_id":"C2","capacity":3,"waypoints":[(40,-25),(35,-17),(31,-8),(34,1),(31,10),(28,19),(25,26),(23,30)]},
}
STATUS_SPEED={"IDLE":0,"LOADING":0,"HAULING":30,"QUEUED":0,"DUMPING":0,"RETURNING":34,"MAINTENANCE":0}
_lock=threading.RLock(); _thread=None; _stop_event=threading.Event(); _generation=0
simulation={"status":"NOT_STARTED","simulation_time_minutes":0,"tick":0,"started_at":None,"paused_at":None,"scenario":"TRACEABLE_CORE_OPERATIONS"}

def _now(): return datetime.now().isoformat()
def _emit(cause,effect,entity,severity="INFO"): add_causal_event(cause,effect,entity,severity)
def _get(name,eid): return next((x for x in mine_state.get(name,[]) if x.get("entity_id")==eid),None)
def _route_for(t):
    rid=t.get("route_id") or ("R1" if t["entity_id"] in {"T12","T13","T14"} else "R2"); t["route_id"]=rid; return ROUTES[rid]
def _seg(a,b): return math.hypot(b[0]-a[0],b[1]-a[1])
def _lengths(points):
    ls=[_seg(points[i],points[i+1]) for i in range(len(points)-1)]; return ls,sum(ls)
def _position(points,d):
    ls,total=_lengths(points); d=max(0,min(float(d),total)); travelled=0
    for i,l in enumerate(ls):
        if d<=travelled+l or i==len(ls)-1:
            q=0 if l==0 else (d-travelled)/l; a,b=points[i],points[i+1]
            return a[0]+(b[0]-a[0])*q,a[1]+(b[1]-a[1])*q,i
        travelled+=l
    return *points[-1],len(points)-2

def _sync(t):
    pts=_route_for(t)["waypoints"]; _,total=_lengths(pts); d=max(0,min(float(t.get("route_distance",0)),total)); x,z,s=_position(pts,d)
    t.update({"route_distance":round(d,3),"route_segment":s,"route_progress":round(d/total*100,1) if total else 0}); t["position"].update({"x":round(x,2),"z":round(z,2)})
def _advance(t,kmh,direction):
    _,total=_lengths(_route_for(t)["waypoints"]); step=max(.35,kmh/30); t["route_distance"]=float(t.get("route_distance",0))+step*direction
    arrived=t["route_distance"]>=total if direction>0 else t["route_distance"]<=0; t["route_distance"]=max(0,min(t["route_distance"],total)); _sync(t); return arrived

def _set_status(t,status):
    if t.get("status")==status:return
    old=t.get("status","UNKNOWN"); t.update({"status":status,"state_ticks":0,"speed":STATUS_SPEED[status]})
    _emit(f"{t['entity_id']} state changed from {old} to {status}",f"Dispatch cycle advanced for {t['entity_id']}",t["entity_id"])

def _ensure(t,index):
    route=_route_for(t); _,total=_lengths(route["waypoints"])
    defaults={"vehicle_type":"HAUL_TRUCK","payload_capacity":45.0,"operating_hours":820+index*137.5,"trips_completed":0,"material_moved":0.0,"maintenance_ticks":0,"state_ticks":0,"engine_health":float(t.get("health_score",90)),"brake_health":float(max(55,t.get("health_score",90)-4)),"tire_health":float(max(60,t.get("health_score",90)-2)),"hydraulic_health":float(max(58,t.get("health_score",90)-3)),"assignment_id":f"HAUL-{t['entity_id']}","pit_id":route["pit_id"],"dump_id":route["dump_id"],"queue_position":None}
    for k,v in defaults.items(): t.setdefault(k,v)
    initial={"T12":("LOADING",0,0),"T13":("IDLE",0,0),"T14":("IDLE",0,0),"T15":("LOADING",0,0),"T16":("IDLE",0,0)}
    if not t.get("fleet_initialized"):
        st,d,p=initial.get(t["entity_id"],("IDLE",0,0)); t.update({"status":st,"route_distance":d,"payload":p,"batch_id":None,"fleet_initialized":True})
    t["speed"]=STATUS_SPEED.get(t["status"],0); _sync(t)
def _health(t): return round(sum(t[k] for k in ("engine_health","brake_health","tire_health","hydraulic_health"))/4)

def _crusher_queue(crusher_id):
    return sorted([t for t in mine_state["trucks"] if t.get("dump_id")==crusher_id and t["status"]=="QUEUED"],key=lambda x:x.get("queue_entered_tick",0))
def _can_dump(t):
    c=_get("crushers",t["dump_id"]); dumping=next((x for x in mine_state["trucks"] if x.get("dump_id")==t["dump_id"] and x["status"]=="DUMPING"),None)
    q=_crusher_queue(t["dump_id"]); return c and c["status"]!="OFFLINE" and dumping is None and q and q[0]["entity_id"]==t["entity_id"]

def _new_batch(t):
    trace=mine_state["traceability"]; n=trace["next_batch_number"]; batch_id=f"B-{n:04d}"; trace["next_batch_number"]+=1; trace["batches_created"]+=1
    pit=_get("pits",t["pit_id"]); qty=float(t["payload_capacity"])
    mine_state["ore_passports"][batch_id]={"batch_id":batch_id,"origin":pit["entity_id"],"origin_name":pit["name"],"grade_fe":pit["ore_grade"],"quantity_mt":qty,"carrier":t["entity_id"],"route_id":t["route_id"],"destination":t["dump_id"],"current_stage":"PIT","current_entity":pit["entity_id"],"status":"CREATED","custody_owner":"PIT_OPERATIONS","processed_mt":0.0,"stockpiled_mt":0.0,"trace_events":[]}
    t["batch_id"]=batch_id; add_trace_event(batch_id,"BATCH_CREATED",pit["entity_id"],"PIT","PIT_OPERATIONS",simulation["simulation_time_minutes"]); return batch_id

def _trace(t,event,entity,stage,owner,status=None):
    bid=t.get("batch_id")
    if not bid:return
    p=mine_state["ore_passports"].get(bid)
    if status:p["status"]=status
    add_trace_event(bid,event,entity,stage,owner,simulation["simulation_time_minutes"])

def _update_truck(t):
    status=t["status"]; t["state_ticks"]+=1; t["operating_hours"]=round(t["operating_hours"]+1/60,2); t["queue_position"]=None
    if status not in {"IDLE","MAINTENANCE","QUEUED"}: t["fuel"]=round(max(0,t["fuel"]-(0.035 if status in {"LOADING","DUMPING"} else .085)),2)
    if status in {"HAULING","RETURNING"}:
        d=.012 if status=="HAULING" else .008
        for k,m in (("engine_health",1),("brake_health",1.2),("tire_health",.8),("hydraulic_health",.55)): t[k]=max(0,t[k]-d*m)
    t["health_score"]=_health(t)
    if t["health_score"]<=55 and status!="MAINTENANCE": t["maintenance_ticks"]=0; _set_status(t,"MAINTENANCE"); return
    if status=="IDLE" and t["state_ticks"]>=2: _set_status(t,"LOADING")
    elif status=="LOADING":
        if not t.get("batch_id"): _new_batch(t)
        t["payload"]=round(min(t["payload_capacity"],t["payload"]+7.5),1)
        if t["payload"]>=t["payload_capacity"]:
            pit=_get("pits",t["pit_id"]); pit["available_ore"]=round(max(0,pit["available_ore"]-t["payload_capacity"]),1); _trace(t,"ORE_LOADED",t["entity_id"],"LOADED","FLEET_OPERATIONS","IN_TRANSIT"); _trace(t,"HAULAGE_STARTED",t["route_id"],"HAULAGE","FLEET_OPERATIONS","IN_TRANSIT"); _set_status(t,"HAULING")
    elif status=="HAULING":
        t["speed"]=round(30+random.uniform(-1.5,1.5),1)
        if _advance(t,t["speed"],1): t["queue_entered_tick"]=simulation["tick"]; _trace(t,"CRUSHER_QUEUE_ENTERED",t["dump_id"],"QUEUED","PLANT_OPERATIONS","QUEUED"); _set_status(t,"QUEUED")
    elif status=="QUEUED":
        q=_crusher_queue(t["dump_id"])
        for i,x in enumerate(q): x["queue_position"]=i+1
        if _can_dump(t): _trace(t,"CRUSHER_RECEIVING_STARTED",t["dump_id"],"RECEIVING","PLANT_OPERATIONS","RECEIVING"); _set_status(t,"DUMPING")
    elif status=="DUMPING":
        c=_get("crushers",t["dump_id"]); amount=min(15.0,t["payload"]); t["payload"]=round(t["payload"]-amount,1); c["input_buffer_mt"]=round(c.get("input_buffer_mt",0)+amount,1); c.setdefault("batch_buffer",[]); bid=t.get("batch_id")
        lot=next((x for x in c["batch_buffer"] if x["batch_id"]==bid),None)
        if lot: lot["remaining_mt"]=round(lot["remaining_mt"]+amount,1)
        elif bid: c["batch_buffer"].append({"batch_id":bid,"remaining_mt":amount})
        if t["payload"]<=0:
            moved=float(t["payload_capacity"]); t["trips_completed"]+=1; t["material_moved"]=round(t["material_moved"]+moved,1); mine_state["operations"]["material_dispatched"]=round(mine_state["operations"].get("material_dispatched",0)+moved,1); _trace(t,"BATCH_RECEIVED",t["dump_id"],"CRUSHER","PLANT_OPERATIONS","PROCESSING"); t["batch_id"]=None; _set_status(t,"RETURNING")
    elif status=="RETURNING":
        t["speed"]=round(34+random.uniform(-1.5,1.5),1)
        if _advance(t,t["speed"],-1): _set_status(t,"LOADING")
    elif status=="MAINTENANCE":
        t["maintenance_ticks"]+=1
        if t["maintenance_ticks"]>=15:
            for k in ("engine_health","brake_health","tire_health","hydraulic_health"): t[k]=max(t[k],88)
            t["health_score"]=_health(t); t["fuel"]=max(t["fuel"],75); _set_status(t,"IDLE")

def _process_crushers():
    stock=mine_state["stockyards"][0]; total_processed=0
    for c in mine_state["crushers"]:
        c.setdefault("input_buffer_mt",0.0); c.setdefault("processed_total_mt",0.0); c.setdefault("rated_capacity_mt_h",900 if c["entity_id"]=="C1" else 700); c.setdefault("batch_buffer",[])
        capacity=c["rated_capacity_mt_h"]/60; processed=0.0
        while capacity>0 and c["batch_buffer"]:
            lot=c["batch_buffer"][0]; amount=min(capacity,lot["remaining_mt"]); lot["remaining_mt"]=round(lot["remaining_mt"]-amount,3); capacity-=amount; processed+=amount
            p=mine_state["ore_passports"].get(lot["batch_id"])
            if p: p["processed_mt"]=round(p.get("processed_mt",0)+amount,1)
            if lot["remaining_mt"]<=0.001:
                c["batch_buffer"].pop(0)
                if p and p["processed_mt"]>=p["quantity_mt"]-0.1:
                    p["stockpiled_mt"]=p["quantity_mt"]; p["status"]="STOCKPILED"; add_trace_event(p["batch_id"],"STOCKPILED","SY1","STOCKYARD","MATERIAL_CONTROL",simulation["simulation_time_minutes"]); mine_state["traceability"]["batches_stockpiled"]+=1; mine_state["traceability"]["traced_mass_mt"]=round(mine_state["traceability"]["traced_mass_mt"]+p["quantity_mt"],1)
        c["input_buffer_mt"]=round(sum(x["remaining_mt"] for x in c["batch_buffer"]),1); c["processed_total_mt"]=round(c["processed_total_mt"]+processed,1); c["throughput"]=round(processed*60); total_processed+=processed; stock["inventory"]=round(stock["inventory"]+processed,1); stock["live_inflow_mt"]=round(stock["inventory"]-stock["baseline_inventory"],1)
    stock["capacity_percentage"]=round(min(100,stock["inventory"]/132000*100),1); return total_processed

def _derive(processed):
    trucks=mine_state["trucks"]; ops=mine_state["operations"]; productive=[t for t in trucks if t["status"] not in {"IDLE","MAINTENANCE"}]
    ops.update({"active_trucks":len(productive),"truck_queue":sum(t["status"]=="QUEUED" for t in trucks),"material_in_transit":round(sum(float(t.get("payload",0)) for t in trucks if t["status"]=="HAULING"),1),"fleet_utilization":round(len(productive)/max(len(trucks),1)*100),"production_rate":round(processed*60),"fleet_trips_completed":sum(t.get("trips_completed",0) for t in trucks),"fleet_material_moved":round(sum(t.get("material_moved",0) for t in trucks),1),"average_fleet_health":round(sum(t["health_score"] for t in trucks)/max(len(trucks),1),1)})

def _publish():
    lookup={r["entity_id"]:r for r in mine_state["routes"]}
    for rid,cfg in ROUTES.items():
        r=lookup[rid]; r.update({"waypoints":[{"x":x,"y":0,"z":z} for x,z in cfg["waypoints"]],"pit_id":cfg["pit_id"],"dump_id":cfg["dump_id"],"capacity":cfg["capacity"],"traffic_count":0})
    for c in mine_state["crushers"]: c.update({"input_buffer_mt":0.0,"processed_total_mt":0.0,"rated_capacity_mt_h":900 if c["entity_id"]=="C1" else 700,"batch_buffer":[]})

def _run(gen):
    while not _stop_event.wait(TICK_SECONDS):
        with _lock:
            if gen!=_generation:return
            if simulation["status"]=="PAUSED":continue
            if simulation["status"]!="RUNNING":return
            for i,t in enumerate(mine_state["trucks"]): _ensure(t,i)
            for t in mine_state["trucks"]: _update_truck(t)
            for r in mine_state["routes"]: r["traffic_count"]=sum(t.get("route_id")==r["entity_id"] and t["status"] in {"HAULING","RETURNING"} for t in mine_state["trucks"])
            processed=_process_crushers(); _derive(processed); simulation["tick"]+=1; simulation["simulation_time_minutes"]+=1; process_fleet_tick(simulation["tick"]); mine_state["timestamp"]=_now()

def start_fleet_simulation():
    global _thread,_generation
    with _lock:
        if simulation["status"]=="RUNNING":return {"status":"ALREADY_RUNNING","simulation":get_simulation_state()}
        if simulation["status"]=="PAUSED":return resume_fleet_simulation()
        _generation+=1; _stop_event.clear(); _publish()
        for i,t in enumerate(mine_state["trucks"]): _ensure(t,i)
        _derive(0); simulation.update({"status":"RUNNING","simulation_time_minutes":0,"tick":0,"started_at":_now(),"paused_at":None,"scenario":"TRACEABLE_CORE_OPERATIONS"}); _emit("Core operations simulation started","Dispatch, haulage and processing stream active","MINE-01")
        _thread=threading.Thread(target=_run,args=(_generation,),daemon=True); _thread.start(); return {"status":"SIMULATION_STARTED","simulation":get_simulation_state()}
def pause_fleet_simulation():
    with _lock:
        if simulation["status"]!="RUNNING":return {"status":"NOT_RUNNING","simulation":get_simulation_state()}
        simulation.update({"status":"PAUSED","paused_at":_now()}); return {"status":"SIMULATION_PAUSED","simulation":get_simulation_state()}
def resume_fleet_simulation():
    with _lock:
        if simulation["status"]!="PAUSED":return {"status":"NOT_PAUSED","simulation":get_simulation_state()}
        simulation.update({"status":"RUNNING","paused_at":None}); return {"status":"SIMULATION_RESUMED","simulation":get_simulation_state()}
def reset_fleet_simulation():
    global _generation
    with _lock:
        _generation+=1; _stop_event.set(); simulation.update({"status":"NOT_STARTED","simulation_time_minutes":0,"tick":0,"started_at":None,"paused_at":None,"scenario":"TRACEABLE_CORE_OPERATIONS"}); return {"status":"FLEET_SIMULATION_RESET"}
def get_simulation_state(): return dict(simulation)
