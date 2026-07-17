from datetime import datetime, timezone
import json
from auth_service import _db

_data_sources = [
    {"id":"SRC-FLEET","name":"Fleet Simulation Stream","type":"TELEMETRY_API","status":"CONNECTED","records":"LIVE"},
    {"id":"SRC-TOPO","name":"Mine Topology","type":"OPERATIONAL_MODEL","status":"CONNECTED","records":7},
]
def _now(): return datetime.now(timezone.utc).isoformat()
def reset_product_services(workspace_id=None):
    if workspace_id is None: return
    with _db() as c:
        c.execute('DELETE FROM ingestions WHERE workspace_id=?',(workspace_id,)); c.execute('DELETE FROM vision_events WHERE workspace_id=?',(workspace_id,))
def get_data_sources(workspace_id):
    with _db() as c: rows=c.execute('SELECT * FROM ingestions WHERE workspace_id=? ORDER BY id DESC LIMIT 20',(workspace_id,)).fetchall()
    ing=[{'id':f"ING-{r['id']:03d}",'name':r['name'],'status':r['status'],'row_count':r['row_count'],'columns':json.loads(r['columns_json']),'sample':json.loads(r['sample_json']),'created_at':r['created_at']} for r in rows]
    return {'sources':[dict(x,last_sync=_now()) for x in _data_sources],'ingestions':ing}
def ingest_dataset(workspace_id,payload):
    rows=payload.get('rows') or []; columns=payload.get('columns') or []; name=(payload.get('name') or 'dataset.csv')[:120]
    if not rows or not columns: return {'status':'REJECTED','message':'Dataset must contain headers and at least one row'}
    with _db() as c: iid=c.execute('INSERT INTO ingestions(workspace_id,name,row_count,columns_json,sample_json,status,created_at) VALUES(?,?,?,?,?,?,?)',(workspace_id,name,len(rows),json.dumps(columns[:30]),json.dumps(rows[:5]),'INGESTED',_now())).lastrowid
    return {'id':f'ING-{iid:03d}','name':name,'status':'INGESTED','row_count':len(rows),'columns':columns[:30],'sample':rows[:5],'created_at':_now()}
def record_vision_event(workspace_id,payload):
    camera=payload.get('camera_id') or 'CAM-04'; detections=payload.get('detections') or []; queue=next((d for d in detections if d.get('label')=='QUEUE_EVENT'),{}); severity='WARNING' if int(queue.get('count',0) or 0)>0 else 'INFO'; title='Queue formation detected' if severity=='WARNING' else 'Vision analysis completed'; desc=payload.get('description') or 'Computer vision inference produced structured mine observations.'; conf=float(payload.get('confidence',94))
    with _db() as c:
        n=c.execute('SELECT COUNT(*) n FROM vision_events WHERE workspace_id=?',(workspace_id,)).fetchone()['n']+1; eid=f'VIS-{n:03d}'
        c.execute('INSERT INTO vision_events(workspace_id,event_id,camera_id,severity,title,description,confidence,detections_json,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(workspace_id,eid,camera,severity,title,desc,conf,json.dumps(detections),_now()))
    return {'event_id':eid,'timestamp':_now(),'source_type':'VISION_INTELLIGENCE','source_id':camera,'incident_type':'VISION_OPERATIONAL_EVENT','title':title,'description':desc,'severity':severity,'status':'RECORDED','confidence':conf,'detections':detections}
def get_vision_events(workspace_id):
    with _db() as c: rows=c.execute('SELECT * FROM vision_events WHERE workspace_id=? ORDER BY id DESC',(workspace_id,)).fetchall()
    return [{'event_id':r['event_id'],'timestamp':r['created_at'],'source_type':'VISION_INTELLIGENCE','source_id':r['camera_id'],'incident_type':'VISION_OPERATIONAL_EVENT','title':r['title'],'description':r['description'],'severity':r['severity'],'status':'RECORDED','confidence':r['confidence'],'detections':json.loads(r['detections_json'])} for r in rows]


def alert_key(item):
    return str(item.get("incident_id") or item.get("event_id") or f"{item.get('source_id','SYSTEM')}:{item.get('title','ALERT')}")

def get_alerts(workspace_id, incidents):
    vision=get_vision_events(workspace_id)
    alerts=[x for x in incidents if x.get("severity") in {"CRITICAL","HIGH","WARNING"}] + [x for x in vision if x.get("severity")=="WARNING"]
    with _db() as c:
        reads={r["alert_key"] for r in c.execute("SELECT alert_key FROM alert_reads WHERE workspace_id=?",(workspace_id,)).fetchall()}
    enriched=[dict(x, alert_key=alert_key(x), is_read=alert_key(x) in reads) for x in alerts]
    return {"unread_count":sum(not x["is_read"] for x in enriched),"alerts":enriched[:20]}

def mark_alert_read(workspace_id,key):
    with _db() as c: c.execute("INSERT OR REPLACE INTO alert_reads(workspace_id,alert_key,read_at) VALUES(?,?,?)",(workspace_id,key,_now()))
    return {"status":"READ","alert_key":key}

def seed_demo_workspace(workspace_id):
    with _db() as c:
        exists=c.execute("SELECT COUNT(*) n FROM ingestions WHERE workspace_id=?",(workspace_id,)).fetchone()["n"]
    if not exists:
        ingest_dataset(workspace_id,{"name":"north_pit_shift_telemetry.csv","columns":["timestamp","truck_id","payload_mt","fuel_pct","brake_health","route"],"rows":[{"timestamp":"06:00","truck_id":"T12","payload_mt":"45","fuel_pct":"88","brake_health":"94","route":"R1"},{"timestamp":"06:05","truck_id":"T14","payload_mt":"45","fuel_pct":"76","brake_health":"39","route":"R1"},{"timestamp":"06:10","truck_id":"T15","payload_mt":"45","fuel_pct":"81","brake_health":"91","route":"R2"}]})
    return {"status":"DEMO_READY"}

def triage_vision_event(workspace_id, event_id):
    events = get_vision_events(workspace_id)
    event = next((x for x in events if x.get('event_id') == event_id), None)
    if not event:
        from fastapi import HTTPException
        raise HTTPException(404, 'Vision event not found')
    queue = next((d for d in event.get('detections', []) if d.get('label') == 'QUEUE_EVENT'), {})
    queue_count = int(queue.get('count', 0) or 0)
    if queue_count > 0:
        return {
            'event_id': event_id, 'triage_status': 'ACTION_RECOMMENDED', 'priority': 'P2',
            'classification': 'HAUL_ROAD_CONGESTION', 'confidence': event.get('confidence', 94),
            'operational_context': 'Queue formation detected on East Haul Road camera stream.',
            'recommended_action': 'Inspect R2 dispatch spacing and redirect the next available haul cycle to R1 if crusher capacity permits.',
            'next_module': '/app/fleet', 'owner': 'DISPATCH',
        }
    return {'event_id': event_id, 'triage_status': 'MONITOR', 'priority': 'P4', 'classification': 'NO_ACTIONABLE_ANOMALY', 'confidence': event.get('confidence', 94), 'recommended_action': 'Continue monitoring the camera stream.', 'next_module': '/app/incidents', 'owner': 'OPERATIONS'}
