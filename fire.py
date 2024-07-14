import os
import requests
import json

from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv('TOKEN')
# Replace FNAME with the ID of the firewall you want to update
FNAME = os.getenv('FNAME')
TOKEEP = os.getenv('TOKEEP')
EPHEMERAL = os.getenv('EPHEMERAL')

def get_public_ip():
    response = requests.get('https://api.ipify.org?format=json')
    return response.json()['ip']

def get_public_ipv6():
    response = requests.get('https://api64.ipify.org?format=json')
    return response.json()['ip']

def fetch_cloudflare_ips():
    ipv4_response = requests.get('https://www.cloudflare.com/ips-v4')
    ipv6_response = requests.get('https://www.cloudflare.com/ips-v6')
    ipv4_response.raise_for_status()
    ipv6_response.raise_for_status()
    
    ipv4_ranges = ipv4_response.text.splitlines()
    ipv6_ranges = ipv6_response.text.splitlines()
    
    return ipv4_ranges, ipv6_ranges

def fetch_firewall_rules(firewall_id, token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'https://api.hetzner.cloud/v1/firewalls/{firewall_id}', headers=headers)
    response.raise_for_status()
    data = response.json()
    # print(json.dumps(data, indent=2)) 
    return data

def update_firewall_rules(firewall_id, token, rules):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = {'rules': rules}
    # print(f"Request payload: {json.dumps(data, indent=2)}")
    response = requests.post(f'https://api.hetzner.cloud/v1/firewalls/{firewall_id}/actions/set_rules', headers=headers, data=json.dumps(data))
    if response.status_code not in (200, 201):
        print(f"Failed to update rules. Status code: {response.status_code}")
        print(f"Response: {response.text}")
    response.raise_for_status()
    return response.json()

def main():
    # Fetch current public IPs
    current_ipv4 = get_public_ip()
    current_ipv6 = get_public_ipv6()

    current_ipv4_cidr = f"{current_ipv4}/32"
    current_ipv6_cidr = f"{current_ipv6}/128"

    print(f"Current IPv4: {current_ipv4_cidr}")
    print(f"Current IPv6: {current_ipv6_cidr}")

    # Fetch Cloudflare IPs
    ipv4_ranges, ipv6_ranges = fetch_cloudflare_ips()
    cloudflare_source_ips = ipv4_ranges + ipv6_ranges
    print(f"Cloudflare IPs: {cloudflare_source_ips}")

    # Fetch existing firewall rules
    firewall_data = fetch_firewall_rules(FNAME, TOKEN)
    existing_rules = firewall_data['firewall']['rules']

    # Filter out the old Cloudflare rule and the personal rule
    other_rules = [rule for rule in existing_rules if rule['description'] not in [TOKEEP, EPHEMERAL]]

    # Create new Cloudflare rule with the updated IPs
    new_cloudflare_rule = {
        "direction": "in",
        "protocol": "tcp",
        "port": "443",  # Adjust the port as needed
        "source_ips": cloudflare_source_ips,
        "destination_ips": [],
        "description": TOKEEP
    }

    # Create new personal rule with the current IPs
    new_personal_rule = {
        "direction": "in",
        "protocol": "tcp",
        "port": "any",
        "source_ips": [current_ipv4_cidr, current_ipv6_cidr],
        "destination_ips": [],
        "description": EPHEMERAL
    }

    # Combine the rules
    combined_rules = other_rules + [new_cloudflare_rule, new_personal_rule]

    # print(f"Combined Rules: {json.dumps(combined_rules, indent=2)}")

    # Update the firewall with the combined rules
    update_response = update_firewall_rules(FNAME, TOKEN, combined_rules)

    if 'error' in update_response:
        print(f"Error: {update_response['error']['message']}")
        print(f"Response: {json.dumps(update_response, indent=2)}")
    else:
        print("Firewall rules updated successfully.")

if __name__ == "__main__":
    main()
