from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    Duration
)
from constructs import Construct

class Ec2NlbStack(Stack):

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
            key_name="CDKmy-keypair"  # must exist in AWS
        )

        # User Data: install Apache and sample app
        ec2_instance.add_user_data(
            "sudo yum update -y",
            "sudo yum install -y httpd",
            "sudo systemctl start httpd",
            "sudo systemctl enable httpd",
            "echo '<h1>Hello from EC2 behind NLB!</h1>' | sudo tee /var/www/html/index.html"
        )

        # Network Load Balancer
        nlb = elbv2.NetworkLoadBalancer(
            self, "CDKmyNLB",
            vpc=vpc,
            internet_facing=True
        )

        # Target Group with health check
        target_group = elbv2.NetworkTargetGroup(
            self, "CDKmyTargetGroup",
            vpc=vpc,
            port=80,
            targets=[elbv2.InstanceTarget(ec2_instance.instance_id, port=80)],
            health_check=elbv2.HealthCheck(
                port="80",
                protocol=elbv2.Protocol.TCP,
                healthy_threshold_count=2,
                unhealthy_threshold_count=2,
                interval=Duration.seconds(30)
            )
        )

        # Listener
        nlb.add_listener(
            "CDKmyListener",
            port=80,
            default_target_groups=[target_group]
        )
