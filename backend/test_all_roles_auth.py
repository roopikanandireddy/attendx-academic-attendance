import urllib.request
import json

def test_auth_and_user_fetch(role_name, email, password, dashboard_endpoint):
    url = 'http://127.0.0.1:8000/api/auth/login'
    data = json.dumps({'email': email, 'password': password}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    with urllib.request.urlopen(req) as resp:
        res_data = json.loads(resp.read().decode())
        token = res_data['access_token']
        user = res_data['user']
        print(f"=== {role_name.upper()} LOGIN SUCCESS ===")
        print(f"User ID:    {user['id']}")
        print(f"Email:      {user['email']}")
        print(f"Full Name:  {user['full_name']}")
        print(f"Role:       {user['role']}")
        print(f"Status:     {user.get('account_status')}")
        
        # Test /api/auth/me with Bearer token
        me_req = urllib.request.Request('http://127.0.0.1:8000/api/auth/me', headers={
            'Authorization': f'Bearer {token}'
        })
        with urllib.request.urlopen(me_req) as me_resp:
            me_data = json.loads(me_resp.read().decode())
            print(f"Me check:   Verified as {me_data['full_name']} ({me_data['role']})")
            
        # Test role-specific dashboard endpoint
        dash_req = urllib.request.Request(f'http://127.0.0.1:8000{dashboard_endpoint}', headers={
            'Authorization': f'Bearer {token}'
        })
        with urllib.request.urlopen(dash_req) as dash_resp:
            dash_data = json.loads(dash_resp.read().decode())
            print(f"Dashboard:  HTTP {dash_resp.status} OK at {dashboard_endpoint}")
            keys = list(dash_data.keys())[:4]
            print(f"Data keys:  {keys}")
        print()

if __name__ == '__main__':
    print("-" * 65)
    print("ATTENDX AUTHENTICATION & ROLE DASHBOARD ACCESS VERIFICATION")
    print("-" * 65)
    test_auth_and_user_fetch('Student', 'john.doe@student.com', 'StudentPassword123!', '/api/dashboard/student')
    test_auth_and_user_fetch('Lecturer', 'dr.alan@lecturer.com', 'LecturerPassword123!', '/api/dashboard/lecturer')
    test_auth_and_user_fetch('Admin', 'admin@attendx.com', 'AdminPassword123!', '/api/admin/dashboard')
