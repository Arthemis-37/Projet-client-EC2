from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import boto3
import os

ec2_client = boto3.client('ec2')

ALLOWED_AMIS = {"1": "ami-030d567be676a90e0", "2": "ami-05b5a865c3579bbc4", "3": "ami-0eeeb6788f77d3616"}
ADAPTED_LAB_AMIS = {
    "ami-030d567be676a90e0": "ami-0c614dee691cbbf37",
    "ami-05b5a865c3579bbc4": "ami-0c7217cdde317cfec",
    "ami-0eeeb6788f77d3616": "ami-058bd2d568351da34"
}

class AWSWhitePageConsoleHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            ec2_rows, vpc_rows, subnet_rows, igw_rows = "", "", "", ""
            vpc_options, subnet_options = "", ""

            try:
                # LISTER LES INSTANCES
                ec2_data = ec2_client.describe_instances()
                for reservation in ec2_data['Reservations']:
                    for inst in reservation['Instances']:
                        if inst['State']['Name'] == 'terminated': continue
                        name = next((t['Value'] for t in inst.get('Tags', []) if t['Key'] == 'Name'), "Machine Perso")
                        statut = inst['State']['Name']
                        badge = "success" if statut == "running" else "danger" if statut == "stopped" else "warning"
                        trad = "Allumé" if statut == "running" else "Arrêté" if statut == "stopped" else "En suppression..."
                        ami_prof = next((k for k, v in ADAPTED_LAB_AMIS.items() if v == inst['ImageId']), inst['ImageId'])
                        
                        ec2_rows += f"""
                        <tr>
                            <td><strong>{name}</strong></td>
                            <td><code>{inst['InstanceId']}</code></td>
                            <td><span class="badge" style="background:#eee; color:#333;">{inst['InstanceType']}</span></td>
                            <td>{ami_prof}</td>
                            <td><span class="badge bg-{badge}">{trad}</span></td>
                            <td>
                                <form action="/supprimer-ec2" method="POST" style="display:inline;">
                                    <input type="hidden" name="instance_id" value="{inst['InstanceId']}">
                                    <button type="submit" class="btn-danger">Supprimer</button>
                                </form>
                            </td>
                        </tr>
                        """

                # LISTER LES VPCS (FILTRÉ)
                vpc_data = ec2_client.describe_vpcs()['Vpcs']
                for vpc in vpc_data:
                    if vpc.get('IsDefault', False): continue
                    v_id, cidr = vpc['VpcId'], vpc['CidrBlock']
                    vpc_options += f'<option value="{v_id}">{v_id} ({cidr})</option>'
                    
                    vpc_rows += f"""
                    <tr>
                        <td><code>{v_id}</code></td>
                        <td><span class="badge" style="background:#232f3e; color:white;">{cidr}</span></td>
                        <td>Aucun</td>
                        <td>Non</td>
                        <td><span class="badge bg-success">{vpc['State']}</span></td>
                        <td>
                            <form action="/supprimer-vpc" method="POST" style="display:inline;">
                                <input type="hidden" name="vpc_id" value="{v_id}">
                                <button type="submit" class="btn-danger">Supprimer VPC</button>
                            </form>
                        </td>
                    </tr>
                    """

                # LISTER LES SUBNETS (FILTRÉ)
                sub_data = ec2_client.describe_subnets()['Subnets']
                for sub in sub_data:
                    if sub['VpcId'] not in vpc_options: continue
                    s_id, v_id, s_cidr = sub['SubnetId'], sub['VpcId'], sub['CidrBlock']
                    subnet_options += f'<option value="{s_id}">{s_id} ({s_cidr})</option>'
                    
                    subnet_rows += f"""
                    <tr>
                        <td><code>{s_id}</code></td>
                        <td><code>{v_id}</code></td>
                        <td><span class="badge" style="background:#eee; color:#333;">{s_cidr}</span></td>
                        <td><strong>{sub['AvailableIpAddressCount']}</strong></td>
                        <td>
                            <form action="/supprimer-subnet" method="POST" style="display:inline;">
                                <input type="hidden" name="subnet_id" value="{s_id}">
                                <button type="submit" class="btn-danger">Supprimer</button>
                            </form>
                        </td>
                    </tr>
                    """

                # LISTER LES IGWS
                igw_data = ec2_client.describe_internet_gateways()['InternetGateways']
                for igw in igw_data:
                    att = igw.get('Attachments', [])
                    vpc_att = att[0]['VpcId'] if att else "Détachée"
                    if vpc_att != "Détachée" and vpc_att not in vpc_options: continue
                    
                    igw_rows += f"""
                    <tr>
                        <td><code>{igw['InternetGatewayId']}</code></td>
                        <td><code>{vpc_att}</code></td>
                        <td>
                            <form action="/supprimer-igw" method="POST" style="display:inline;">
                                <input type="hidden" name="igw_id" value="{igw['InternetGatewayId']}">
                                <button type="submit" class="btn-danger">Supprimer</button>
                            </form>
                        </td>
                    </tr>
                    """

            except Exception as e: print(f"Erreur lecture : {e}")

            if not ec2_rows: ec2_rows = "<tr><td colspan='6' style='text-align:center; color:#999;'>Aucune machine.</td></tr>"
            if not vpc_rows: vpc_rows = "<tr><td colspan='6' style='text-align:center; color:#999;'>Aucun VPC personnalisé.</td></tr>"
            if not subnet_rows: subnet_rows = "<tr><td colspan='5' style='text-align:center; color:#999;'>Aucun sous-réseau.</td></tr>"
            if not igw_rows: igw_rows = "<tr><td colspan='3' style='text-align:center; color:#999;'>Aucune passerelle.</td></tr>"

            if os.path.exists("index.html"):
                with open("index.html", "r", encoding="utf-8") as f: html = f.read()
                final = html.replace("{{EC2_ROWS}}", ec2_rows).replace("{{VPC_ROWS}}", vpc_rows)\
                            .replace("{{SUBNET_ROWS}}", subnet_rows).replace("{{IGW_ROWS}}", igw_rows)\
                            .replace("{{VPC_OPTIONS}}", vpc_options).replace("{{SUBNET_OPTIONS}}", subnet_options)
                self.wfile.write(final.encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        params = urllib.parse.parse_qs(self.rfile.read(content_length).decode('utf-8'))

        # --- ROUTE CRÉATION EC2 ---
        if self.path == "/creer-ec2":
            choix, sub_id = params.get('choix_ami', [''])[0], params.get('subnet_id', [''])[0]
            if choix in ALLOWED_AMIS and sub_id:
                ami_to_deploy = ADAPTED_LAB_AMIS.get(ALLOWED_AMIS[choix], ALLOWED_AMIS[choix])
                try:
                    ec2_client.run_instances(ImageId=ami_to_deploy, InstanceType='t3.micro', MinCount=1, MaxCount=1, SubnetId=sub_id,
                                             TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': 'Machine Perso'}]}])
                    print("Ordre AWS : Création de l'instance envoyé.")
                except Exception as e: print(f"Erreur : {e}")

        # --- ROUTE SUPPRESSION EC2 ---
        elif self.path == "/supprimer-ec2":
            inst_id = params.get('instance_id', [''])[0]
            if inst_id:
                try:
                    ec2_client.terminate_instances(InstanceIds=[inst_id])
                    print(f"Ordre AWS : Demande de suppression pour {inst_id} validée.")
                except Exception as e: print(f"Erreur suppression EC2 : {e}")

        # --- ROUTE CRÉATION VPC ---
        elif self.path == "/creer-vpc":
            cidr = params.get('cidr_block', [''])[0].strip()
            try: 
                ec2_client.create_vpc(CidrBlock=cidr)
                print(f"Ordre AWS : Création du VPC {cidr} envoyé.")
            except Exception as e: print(f"Erreur VPC : {e}")

        # --- ROUTE SUPPRESSION VPC (CASCADE INTÉGRÉE) ---
        elif self.path == "/supprimer-vpc":
            vpc_id = params.get('vpc_id', [''])[0]
            if vpc_id:
                try:
                    print(f"Lancement du nettoyage cascade pour le VPC {vpc_id}...")
                    # Suppression des sous-réseaux dépendants
                    subnets = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']
                    for sub in subnets:
                        try: 
                            ec2_client.delete_subnet(SubnetId=sub['SubnetId'])
                            print(f"Sous-réseau {sub['SubnetId']} supprimé.")
                        except Exception as es: print(f" Échec sous-réseau : {es}")
                    
                    # Suppression définitive du VPC
                    ec2_client.delete_vpc(VpcId=vpc_id)
                    print(f"Succès global : Le VPC {vpc_id} a été supprimé d'AWS.")
                except Exception as e: print(f"Erreur suppression VPC : {e}")

        # --- ROUTE CRÉATION SUBNET ---
        elif self.path == "/creer-subnet":
            vpc_id, cidr = params.get('vpc_id', [''])[0], params.get('cidr_block', [''])[0].strip()
            try: 
                ec2_client.create_subnet(VpcId=vpc_id, CidrBlock=cidr)
                print(f"Ordre AWS : Création du sous-réseau {cidr} envoyé.")
            except Exception as e: print(f"Erreur sous-réseau : {e}")

        # --- ROUTE SUPPRESSION SUBNET ---
        elif self.path == "/supprimer-subnet":
            sub_id = params.get('subnet_id', [''])[0]
            if sub_id:
                try:
                    ec2_client.delete_subnet(SubnetId=sub_id)
                    print(f"Ordre AWS : Sous-réseau {sub_id} supprimé.")
                except Exception as e: print(f"Erreur suppression sous-réseau : {e}")

        # --- ROUTE PASSERELLE ---
        elif self.path == "/creer-igw":
            try: ec2_client.create_internet_gateway()
            except Exception as e: print(f"Erreur IGW : {e}")

        elif self.path == "/supprimer-igw":
            igw_id = params.get('igw_id', [''])[0]
            try: ec2_client.delete_internet_gateway(InternetGatewayId=igw_id)
            except Exception as e: print(f"Erreur IGW : {e}")

        # Redirection d'actualisation de la page blanche
        self.send_response(303)
        self.send_header('Location', '/')
        self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('', 5000), AWSWhitePageConsoleHandler)
    print("lancé sur : http://127.0.0.1:5000")
    try: server.serve_forever()
    except KeyboardInterrupt: server.server_close()