"""Run against a live local backend: python3 smoke_test.py"""
import json, time, urllib.request, uuid, os
BASE=os.getenv('API_URL','http://127.0.0.1:8000')
def req(path,data=None,token=None):
    h={'Content-Type':'application/json'}
    if token: h['Authorization']='Bearer '+token
    r=urllib.request.Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,headers=h,method='POST' if data is not None else 'GET')
    return json.load(urllib.request.urlopen(r,timeout=10))
email=f'qa-{uuid.uuid4().hex[:8]}@minemind.local'
s=req('/auth/signup',{'name':'QA Operator','email':email,'password':'minemind123','mine':'QA Mine'}); token=s['token']
assert req('/workspace/demo-launch',{},token)['status']=='DEMO_RUNNING'
assert req('/data-sources/state',token=token)['ingestions']
v=req('/vision/events',{'camera_id':'CAM-04','detections':[{'label':'QUEUE_EVENT','count':1,'confidence':94}],'confidence':94},token)
assert req(f"/vision/events/{v['event_id']}/triage",{},token)['triage_status']=='ACTION_RECOMMENDED'
assert req('/alerts/state',token=token)['unread_count']>=1
assert req('/incidents/state',token=token)['engine_status']=='AUDIT_ACTIVE'
print('MINEMIND FINAL SMOKE TEST: PASS')
