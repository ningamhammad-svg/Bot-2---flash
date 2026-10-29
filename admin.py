from flask import Blueprint, request
from storage import get_all_chats, get_control_data, save_control_data
import os

admin_bp = Blueprint('admin', __name__)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "NEGRO342")

@admin_bp.route('/admin/<business_id>')
def admin_panel(phone_number_id):
    token = request.args.get("token")
    if token != VERIFY_TOKEN:
        return "Token si sahihi", 403
    
    chats_data = get_all_chats()
    control_data = get_control_data()
    all_chats = chats_data.get(phone_number_id, {})
    
    html_content = ''
    for cust_num, chats in all_chats.items():
        is_paused = cust_num in control_data.get("paused_customers", [])
        if is_paused:
            status_html = f'<div style="background:#ff000022;color:red;padding:8px;text-align:center;border-radius:8px">SLEEP - Wewe unaongea</div><a href="/admin/{business_id}/control?token={token}&action=resume&customer={cust_num}" style="background:green;color:white;padding:10px;border-radius:20px;text-decoration:none;display:inline-block;margin:5px">AMSHA BOT</a>'
        else:
            status_html = f'<div style="background:#00ff0022;color:green;padding:8px;text-align:center;border-radius:8px">AWAKE - Bot anajibu</div><a href="/admin/{business_id}/control?token={token}&action=pause&customer={cust_num}" style="background:red;color:white;padding:10px;border-radius:20px;text-decoration:none;display:inline-block;margin:5px">LALAZA BOT</a>'
        
        msgs = ''
        for c in chats[-10:]:
            color = '#dbeafe' if c.get('role') == 'customer' else '#dcfce7'
            msgs += f'<div style="background:{color};padding:8px;margin:5px;border-radius:10px;color:black">{c.get("role")}: {c.get("msg")}<br><small>{c.get("time")}</small></div>'
        
        html_content += f'<div style="background:#1e293b;margin:15px 0;padding:12px;border-radius:12px"><h3>{cust_num}</h3>{status_html}<a href="https://wa.me/{cust_num}" target="_blank" style="background:#25D366;color:white;padding:10px;border-radius:20px;text-decoration:none;display:inline-block;margin:5px">JIBU WA</a><hr>{msgs}</div>'

    full_html = f'''
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>NCIP ADMIN</title></head>
    <body style="font-family:sans-serif;background:#0f172a;color:white;padding:10px">
    <div style="background:linear-gradient(90deg,#ff8a00,#2b6cb0);padding:15px;border-radius:12px;text-align:center">
    <h2>NCIP - BOT CONTROL</h2><p>{phone_number_id}</p></div>
    <h3 style="text-align:center">Wateja: {len(all_chats)}</h3>
    {html_content}
    </body></html>
    '''
    return full_html

@admin_bp.route('/admin/<business_id>/control')
def admin_control(phone_number_id):
    token = request.args.get("token")
    action = request.args.get("action")
    customer = request.args.get("customer")
    if token != VERIFY_TOKEN:
        return "Token si sahihi", 403
    control = get_control_data()
    if action == "pause" and customer:
        if customer not in control["paused_customers"]:
            control["paused_customers"].append(customer)
    elif action == "resume" and customer:
        if customer in control["paused_customers"]:
            control["paused_customers"].remove(customer)
    save_control_data(control)
    return f'<script>alert("Imefanikiwa: {action}"); window.location.href="/admin/{phone_number_id}?token={token}";</script>'
