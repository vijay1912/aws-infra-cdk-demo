from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    Duration
)
from constructs import Construct

class Ec2AlbStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # VPC
        vpc = ec2.Vpc(self, "CDKmyVpc", max_azs=2)

        # Security Group
        sg = ec2.SecurityGroup(
            self, "CDKmySecurityGroup",
            vpc=vpc,
            description="Allow SSH and HTTP",
            allow_all_outbound=True
        )
        sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "Allow SSH")
        sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP")

        # EC2 Instance
        ec2_instance = ec2.Instance(
            self, "CDKmyInstance",
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ec2.MachineImage.latest_amazon_linux2(),
            vpc=vpc,
            security_group=sg,
            key_pair=ec2.KeyPair.from_key_pair_name(self, "CDKmyKeyPair", "CDKmy-keypair")
        )

        # User Data: install Apache
        ec2_instance.add_user_data(
            "sudo yum update -y",
            "sudo yum install -y httpd",
            "sudo systemctl start httpd",
            "sudo systemctl enable httpd",
            "echo '<h1>Hello from EC2 behind ALB!</h1>' | sudo tee /var/www/html/index.html"
        )

        # Application Load Balancer
        alb = elbv2.ApplicationLoadBalancer(
            self, "CDKmyALB",
            vpc=vpc,
            internet_facing=True,
            security_group=sg
        )

        # Listener
        listener = alb.add_listener("Listener", port=80)

        # Target Group (attach EC2 instance)
        listener.add_targets("AppFleet",
            port=80,
            targets=[ec2_instance],
            health_check=elbv2.HealthCheck(
                path="/",
                port="80",
                protocol=elbv2.Protocol.HTTP,
                healthy_threshold_count=2,
                unhealthy_threshold_count=2,
                interval=Duration.seconds(30)
            )
        )
